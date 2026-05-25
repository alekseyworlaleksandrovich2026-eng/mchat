import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { ArrowLeft, BookOpen, FileUp, Plus, Trash2 } from 'lucide-react'
import { portalApi, type ChannelKnowledgeBase } from '@/lib/portalApi'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'

export function ChannelKnowledgePage() {
  const { t } = useTranslation()
  const { id: channelId } = useParams<{ id: string }>()
  const [items, setItems] = useState<ChannelKnowledgeBase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)
  const [uploadingKb, setUploadingKb] = useState<string | null>(null)
  const [removingKb, setRemovingKb] = useState<string | null>(null)

  const load = async () => {
    if (!channelId) return
    setLoading(true)
    setError(null)
    try {
      const list = await portalApi.listChannelKnowledgeBases(channelId)
      setItems(list)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Load failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [channelId])

  const handleCreate = async () => {
    if (!channelId || !newName.trim()) return
    setCreating(true)
    try {
      await portalApi.createChannelKnowledgeBase(channelId, { name: newName.trim() })
      setNewName('')
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Create failed')
    } finally {
      setCreating(false)
    }
  }

  const handleUpload = async (kbId: string, file: File | undefined) => {
    if (!channelId || !file) return
    setUploadingKb(kbId)
    setError(null)
    try {
      await portalApi.uploadChannelDocument(channelId, kbId, file)
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploadingKb(null)
    }
  }

  const handleRemove = async (kb: ChannelKnowledgeBase) => {
    if (!channelId) return
    const msg =
      kb.source === 'system'
        ? t(
            'portal.detachSystemKbConfirm',
            'Remove this system knowledge base from the channel? (The library itself will not be deleted.)',
          )
        : t(
            'portal.deleteOwnedKbConfirm',
            'Delete this knowledge base and remove it from the channel?',
          )
    if (!confirm(msg)) return
    setRemovingKb(kb.id)
    setError(null)
    try {
      await portalApi.removeChannelKnowledgeBase(channelId, kb.id)
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Remove failed')
    } finally {
      setRemovingKb(null)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    )
  }

  const systemItems = items.filter((kb) => kb.source === 'system')
  const ownedItems = items.filter((kb) => kb.source !== 'system')

  return (
    <div className="w-full max-w-none space-y-6">
      <Link
        to={`/portal/channels/${channelId}`}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600 dark:text-gray-400"
      >
        <ArrowLeft className="w-4 h-4" />
        {t('portal.myChannels', 'My channels')}
      </Link>

      <div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          {t('portal.channelKnowledgeTitle', 'Channel knowledge')}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t(
            'portal.channelKnowledgeHint',
            'Manage knowledge bases and documents for this channel. RAG uses these during chat.',
          )}
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="rounded-2xl border border-primary-200 dark:border-primary-800 bg-primary-50/80 dark:bg-primary-900/20 p-5">
        <div className="flex gap-3">
          <div className="shrink-0 w-9 h-9 rounded-lg bg-primary-600 text-white flex items-center justify-center">
            <BookOpen className="w-5 h-5" />
          </div>
          <div className="min-w-0 space-y-3">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {t('portal.knowledgeHowToTitle')}
            </h2>
            <ol className="text-sm text-gray-600 dark:text-gray-300 space-y-2 list-decimal list-inside">
              <li>{t('portal.knowledgeStep1')}</li>
              <li>{t('portal.knowledgeStep2')}</li>
              <li>{t('portal.knowledgeStep3')}</li>
              <li>{t('portal.knowledgeStep4')}</li>
            </ol>
            <p className="text-xs text-gray-500 dark:text-gray-400">{t('portal.knowledgeFormats')}</p>
            {systemItems.length > 0 && (
              <p className="text-xs text-violet-700 dark:text-violet-300">{t('portal.knowledgeSystemNote')}</p>
            )}
          </div>
        </div>
      </div>

      {systemItems.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {t('portal.systemKnowledgeBases', 'System knowledge bases')}
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {t(
              'portal.systemKbHint',
              'Provided by the template or platform. Read-only: use in chat, no uploads.',
            )}
          </p>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {systemItems.map((kb) => (
              <KbCard
                key={kb.id}
                kb={kb}
                t={t}
                uploadingKb={uploadingKb}
                removingKb={removingKb}
                onUpload={handleUpload}
                onRemove={handleRemove}
              />
            ))}
          </div>
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {t('portal.ownedKnowledgeBases', 'Your knowledge bases')}
        </h2>
        <div className="flex flex-col sm:flex-row gap-2 sm:items-end">
          <Input
            label={t('portal.newKbName', 'New knowledge base name')}
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="flex-1"
          />
          <Button onClick={handleCreate} isLoading={creating} className="shrink-0 gap-1">
            <Plus className="w-4 h-4" />
            {t('common.create', 'Create')}
          </Button>
        </div>

        {ownedItems.length === 0 && systemItems.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t(
              'portal.noKnowledgeBases',
              'No knowledge bases yet. Create one or rent from a template with KB preset.',
            )}
          </p>
        )}

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {ownedItems.map((kb) => (
            <KbCard
              key={kb.id}
              kb={kb}
              t={t}
              uploadingKb={uploadingKb}
              removingKb={removingKb}
              onUpload={handleUpload}
              onRemove={handleRemove}
            />
          ))}
        </div>
      </section>
    </div>
  )
}

function KbCard({
  kb,
  t,
  uploadingKb,
  removingKb,
  onUpload,
  onRemove,
}: {
  kb: ChannelKnowledgeBase
  t: TFunction
  uploadingKb: string | null
  removingKb: string | null
  onUpload: (kbId: string, file?: File) => void
  onRemove: (kb: ChannelKnowledgeBase) => void
}) {
  const isSystem = kb.source === 'system'
  const canUpload = kb.can_upload !== false && !isSystem

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 flex flex-col gap-3 min-h-[140px]">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-medium text-gray-900 dark:text-gray-100 truncate">{kb.name}</h3>
            <span
              className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded font-medium shrink-0 ${
                isSystem
                  ? 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300'
                  : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
              }`}
            >
              {isSystem
                ? t('portal.kbSourceSystem', 'System')
                : t('portal.kbSourceOwned', 'Self-built')}
            </span>
          </div>
          {kb.description && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{kb.description}</p>
          )}
          <p className="text-xs text-gray-400 mt-2">
            {t('portal.documentCount', {
              count: kb.document_count,
              defaultValue: '{{count}} documents',
            })}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onRemove(kb)}
          disabled={removingKb === kb.id}
          className="shrink-0 p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
          title={
            isSystem
              ? t('portal.detachFromChannel', 'Remove from channel')
              : t('common.delete', 'Delete')
          }
        >
          {removingKb === kb.id ? <Spinner size="sm" /> : <Trash2 className="w-4 h-4" />}
        </button>
      </div>

      <div className="mt-auto flex flex-wrap gap-2">
        {canUpload ? (
          <label className="cursor-pointer">
            <input
              type="file"
              className="hidden"
              accept=".txt,.md,.pdf,.docx,.html"
              disabled={uploadingKb === kb.id}
              onChange={(e) => {
                const f = e.target.files?.[0]
                onUpload(kb.id, f)
                e.target.value = ''
              }}
            />
            <span
              className={`inline-flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 ${
                uploadingKb === kb.id ? 'opacity-50' : 'hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              {uploadingKb === kb.id ? <Spinner size="sm" /> : <FileUp className="w-4 h-4" />}
              {t('portal.uploadDocument', 'Upload')}
            </span>
          </label>
        ) : (
          <span className="text-xs text-gray-400 italic">
            {t('portal.systemKbReadOnly', 'Read-only — no uploads')}
          </span>
        )}
      </div>
    </div>
  )
}
