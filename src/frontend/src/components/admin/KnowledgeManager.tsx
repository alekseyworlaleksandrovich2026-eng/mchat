import React, { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import {
  BookOpen,
  Upload,
  FileText,
  Trash2,
  Search,
  Loader2,
  CheckCircle,
  AlertCircle,
} from 'lucide-react'
import api from '@/lib/api'
import {
  mapDocument,
  mapKnowledgeBase,
  type KnowledgeBase,
  type KnowledgeDocument,
} from '@/lib/knowledgeApi'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Dialog } from '@/components/ui/Dialog'
import { Switch } from '@/components/ui/Switch'
import { toast } from '@/components/ui/Toast'
import { formatDate } from '@/lib/utils'

export function KnowledgeManager() {
  const { t } = useTranslation()
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [milvusEnabled, setMilvusEnabled] = useState(false)
  const [milvusHost, setMilvusHost] = useState('localhost')
  const [milvusPort, setMilvusPort] = useState('19530')
  const [milvusSaving, setMilvusSaving] = useState(false)
  const [milvusTesting, setMilvusTesting] = useState(false)
  const [selectedKB, setSelectedKB] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [kbName, setKbName] = useState('')
  const [kbDesc, setKbDesc] = useState('')
  const [search, setSearch] = useState('')
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const docStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
      case 'indexed':
        return t('knowledge.docStatusCompleted')
      case 'processing':
        return t('knowledge.docStatusProcessing')
      case 'failed':
        return t('knowledge.docStatusFailed')
      default:
        return t('knowledge.docStatusPending')
    }
  }

  useEffect(() => {
    loadKnowledgeBases()
    loadMilvusSettings()
  }, [])

  useEffect(() => {
    if (selectedKB) {
      loadDocuments(selectedKB)
    }
  }, [selectedKB])

  const loadMilvusSettings = async () => {
    try {
      const data = await api.get<Record<string, unknown>>('/settings')
      setMilvusEnabled(Boolean(data.milvus_enabled))
      setMilvusHost(String(data.milvus_host ?? 'localhost'))
      setMilvusPort(String(data.milvus_port ?? 19530))
    } catch (err) {
      console.error('Failed to load Milvus settings:', err)
    }
  }

  const saveMilvusSettings = async () => {
    setMilvusSaving(true)
    try {
      await api.put('/settings', {
        milvus_enabled: milvusEnabled,
        milvus_host: milvusHost,
        milvus_port: Number(milvusPort) || 19530,
      })
      toast(t('knowledge.toastMilvusSaved'), { type: 'success' })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t('common.failed')
      toast(t('knowledge.toastSaveFailed'), { type: 'error', message })
    } finally {
      setMilvusSaving(false)
    }
  }

  const testMilvus = async () => {
    setMilvusTesting(true)
    try {
      const result = await api.post<{ ok: boolean; message: string }>(
        '/settings/milvus/test',
        {
          milvus_enabled: milvusEnabled,
          milvus_host: milvusHost,
          milvus_port: Number(milvusPort) || 19530,
        },
      )
      toast(result.message, { type: result.ok ? 'success' : 'error' })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t('common.failed')
      toast(t('knowledge.toastConnectionTestFailed'), { type: 'error', message })
    } finally {
      setMilvusTesting(false)
    }
  }

  const loadKnowledgeBases = async () => {
    try {
      const data = await api.get<Record<string, unknown>[]>('/knowledge/bases')
      setKnowledgeBases(data.map(mapKnowledgeBase))
    } catch (err) {
      console.error('Failed to load knowledge bases:', err)
      toast(t('knowledge.toastLoadFailed'), { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const loadDocuments = async (kbId: string) => {
    try {
      const data = await api.get<Record<string, unknown>[]>(
        `/knowledge/bases/${kbId}/documents`,
      )
      setDocuments(data.map(mapDocument))
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }

  const handleCreate = async () => {
    if (!kbName.trim()) return
    try {
      const kb = await api.post<Record<string, unknown>>('/knowledge/bases', {
        name: kbName,
        description: kbDesc,
      })
      setKnowledgeBases((prev) => [...prev, mapKnowledgeBase(kb)])
      toast(t('knowledge.toastKbCreated'), { type: 'success' })
      setCreateOpen(false)
      setKbName('')
      setKbDesc('')
    } catch (err) {
      console.error('Failed to create knowledge base:', err)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || !selectedKB) return

    setUploading(true)
    try {
      for (let i = 0; i < files.length; i++) {
        const formData = new FormData()
        formData.append('file', files[i])
        const doc = await api.upload<Record<string, unknown>>(
          `/knowledge/bases/${selectedKB}/import-file`,
          formData,
        )
        const mapped = mapDocument(doc)
        setDocuments((prev) => [...prev, mapped])
        if (mapped.status === 'failed') {
          toast(t('knowledge.toastParseFailed', { name: mapped.filename }), {
            type: 'error',
          })
        }
      }
      toast(t('knowledge.toastUploadComplete'), { type: 'success' })
      loadKnowledgeBases()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t('common.failed')
      toast(t('knowledge.toastUploadFailed'), { type: 'error', message })
      console.error('Failed to upload document:', err)
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleDelete = async (docId: string) => {
    if (!selectedKB) return
    try {
      await api.delete(`/knowledge/documents/${docId}`)
      setDocuments((prev) => prev.filter((d) => d.id !== docId))
    } catch (err) {
      console.error('Failed to delete document:', err)
    }
  }

  const handleDeleteKB = async (kbId: string) => {
    try {
      await api.delete(`/knowledge/bases/${kbId}`)
      setKnowledgeBases((prev) => prev.filter((kb) => kb.id !== kbId))
      if (selectedKB === kbId) {
        setSelectedKB(null)
        setDocuments([])
      }
    } catch (err) {
      console.error('Failed to delete knowledge base:', err)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const filteredDocs = documents.filter((d) =>
    d.filename.toLowerCase().includes(search.toLowerCase()),
  )

  const docStatusVariant = (status: string): 'default' | 'success' | 'warning' | 'danger' => {
    switch (status) {
      case 'completed': return 'success'
      case 'processing': return 'warning'
      case 'failed': return 'danger'
      default: return 'default'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-4 h-full flex flex-col">
      <Card>
        <CardContent className="py-4 space-y-3">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h3 className="text-sm font-medium text-gray-800 dark:text-gray-200">{t('knowledge.milvusTitle')}</h3>
              <p className="text-xs text-gray-500 mt-0.5">
                {t('knowledge.milvusHint')}
              </p>
            </div>
            <Switch checked={milvusEnabled} onChange={setMilvusEnabled} />
          </div>
          {milvusEnabled && (
            <div className="flex flex-wrap gap-3 items-end">
              <Input label={t('knowledge.host')} value={milvusHost} onChange={(e) => setMilvusHost(e.target.value)} className="w-56" />
              <Input label={t('knowledge.port')} value={milvusPort} onChange={(e) => setMilvusPort(e.target.value)} className="w-28" />
              <Button variant="secondary" size="sm" onClick={testMilvus} isLoading={milvusTesting}>{t('knowledge.testConnection')}</Button>
              <Button size="sm" onClick={saveMilvusSettings} isLoading={milvusSaving}>{t('common.save')}</Button>
            </div>
          )}
          {!milvusEnabled && (
            <Button size="sm" variant="secondary" onClick={saveMilvusSettings} isLoading={milvusSaving}>{t('common.save')}</Button>
          )}
        </CardContent>
      </Card>
      <div className="flex gap-6 flex-1 min-h-0">
      {/* Knowledge Base List */}
      <div className="w-72 shrink-0 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('knowledge.kbListTitle')}</h3>
          <Button size="sm" variant="ghost" onClick={() => setCreateOpen(true)}>
            + {t('knowledge.newKb')}
          </Button>
        </div>

        {knowledgeBases.length === 0 ? (
          <Card>
            <CardContent>
              <div className="flex flex-col items-center py-8 text-gray-400">
                <BookOpen className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-xs">{t('knowledge.emptyKb')}</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {knowledgeBases.map((kb) => (
              <Card
                key={kb.id}
                hover
                className={selectedKB === kb.id ? 'ring-2 ring-primary-500' : ''}
                onClick={() => setSelectedKB(kb.id)}
              >
                <CardContent className="py-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {kb.name}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {t('knowledge.documentCount', { count: kb.documentCount })}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteKB(kb.id)
                      }}
                      className="p-1 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Documents */}
      <div className="flex-1 min-w-0">
        {selectedKB ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {t('knowledge.docListTitle')}
              </h3>
              <div className="flex gap-2">
                <Input
                  placeholder={t('knowledge.searchDocsPlaceholder')}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  leftIcon={<Search className="w-4 h-4" />}
                  className="w-60"
                />
                <Button
                  size="actionWide"
                  leftIcon={<Upload className="w-4 h-4" />}
                  onClick={() => {
                    setUploadOpen(true)
                    fileInputRef.current?.click()
                  }}
                >
                  {t('knowledge.uploadDocument')}
                </Button>
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={handleUpload}
              accept=".txt,.pdf,.doc,.docx,.md"
            />

            {filteredDocs.length === 0 ? (
              <Card>
                <CardContent>
                  <div className="flex flex-col items-center py-12 text-gray-400">
                    <FileText className="w-12 h-12 mb-3 opacity-50" />
                    <p className="text-sm">{t('knowledge.emptyDocs')}</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-2">
                {filteredDocs.map((doc) => (
                  <Card key={doc.id}>
                    <CardContent className="py-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 min-w-0">
                          <FileText className="w-5 h-5 text-gray-400 shrink-0" />
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                              {doc.filename}
                            </p>
                            <p className="text-xs text-gray-400">
                              {formatFileSize(doc.fileSize)} · {formatDate(doc.createdAt)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <Badge variant={docStatusVariant(doc.status)} size="sm">
                            {doc.status === 'processing' && (
                              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            )}
                            {doc.status === 'completed' && (
                              <CheckCircle className="w-3 h-3 mr-1" />
                            )}
                            {doc.status === 'failed' && (
                              <AlertCircle className="w-3 h-3 mr-1" />
                            )}
                            {docStatusLabel(doc.status)}
                          </Badge>
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="p-1 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {uploading && (
              <div className="flex items-center justify-center py-4 text-sm text-gray-500">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {t('knowledge.uploading')}
              </div>
            )}
          </div>
        ) : (
          <Card>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                <BookOpen className="w-16 h-16 mb-4 opacity-30" />
                <p className="text-sm">{t('knowledge.selectKbHint')}</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Create Knowledge Base Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title={t('knowledge.dialogCreateKbTitle')} size="sm">
        <div className="space-y-4">
          <Input
            label={t('common.name')}
            value={kbName}
            onChange={(e) => setKbName(e.target.value)}
            placeholder={t('knowledge.kbNamePlaceholder')}
          />
          <Input
            label={t('knowledge.descriptionOptional')}
            value={kbDesc}
            onChange={(e) => setKbDesc(e.target.value)}
            placeholder={t('knowledge.kbDescriptionPlaceholder')}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleCreate} disabled={!kbName.trim()}>
              {t('common.create')}
            </Button>
          </div>
        </div>
      </Dialog>
      </div>
    </div>
  )
}
