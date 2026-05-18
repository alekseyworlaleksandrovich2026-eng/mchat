import React, { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, MessageSquare, MoreVertical, Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '@/lib/api'
import { Conversation } from '@/stores/chat'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { DropdownMenu } from '@/components/ui/DropdownMenu'
import { Dialog } from '@/components/ui/Dialog'
import { formatDate, truncate } from '@/lib/utils'
import { toast } from '@/components/ui/Toast'

interface ConversationListProps {
  onSelect?: (conversation: Conversation) => void
}

export function ConversationList({ onSelect }: ConversationListProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [creating, setCreating] = useState(false)

  const statusOptions = useMemo(
    () => [
      { value: '', label: t('conversations.statusAll') },
      { value: 'active', label: t('conversations.statusActive') },
      { value: 'waiting', label: t('conversations.statusWaiting') },
      { value: 'closed', label: t('conversations.statusClosed') },
    ],
    [t],
  )

  const statusLabels = useMemo(
    (): Record<string, { label: string; variant: 'success' | 'warning' | 'default' }> => ({
      active: { label: t('conversations.statusActive'), variant: 'success' },
      waiting: { label: t('conversations.statusWaiting'), variant: 'warning' },
      closed: { label: t('conversations.statusClosed'), variant: 'default' },
    }),
    [t],
  )

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      const data = await api.get<{ items: Conversation[]; total: number }>('/chat/conversations')
      setConversations(data.items || [])
    } catch (err) {
      console.error('Failed to load conversations:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!newTitle.trim()) return
    setCreating(true)
    try {
      const conv = await api.post<Conversation>('/chat/conversations', { title: newTitle.trim() })
      toast(t('conversations.toastCreateSuccess'), { type: 'success' })
      setShowCreate(false)
      setNewTitle('')
      setConversations([conv, ...conversations])
      navigate(`/chat/${conv.id}`)
    } catch (err: any) {
      toast(t('conversations.toastCreateFailed'), { type: 'error', message: err.message })
    } finally {
      setCreating(false)
    }
  }

  const filtered = conversations.filter((c) => {
    const matchesSearch =
      !search ||
      c.title?.toLowerCase().includes(search.toLowerCase()) ||
      c.visitor_id?.toLowerCase().includes(search.toLowerCase())
    const matchesStatus = !statusFilter || c.status === statusFilter
    return matchesSearch && matchesStatus
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <Input
            placeholder={t('conversations.searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>
        <div className="w-40">
          <Select
            options={statusOptions}
            value={statusFilter}
            onChange={(e: any) => setStatusFilter(e.target.value)}
            placeholder={t('conversations.statusAll')}
          />
        </div>
        <Button leftIcon={<Plus className="w-4 h-4" />} onClick={() => setShowCreate(true)}>
          {t('conversations.createConversation')}
        </Button>
      </div>

      {filtered.length === 0 ? (
        <Card>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <MessageSquare className="w-12 h-12 mb-3 opacity-50" />
              <p className="text-sm mb-4">{t('conversations.emptyList')}</p>
              <Button variant="outline" onClick={() => setShowCreate(true)}>
                {t('conversations.createFirst')}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {filtered.map((conv) => (
            <Card
              key={conv.id}
              hover
              onClick={() => onSelect?.(conv)}
            >
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {conv.title || conv.visitor_id || t('conversations.untitled')}
                        </h3>
                        <Badge
                          variant={statusLabels[conv.status]?.variant || 'default'}
                          size="sm"
                        >
                          {statusLabels[conv.status]?.label || conv.status}
                        </Badge>
                      </div>
                      {conv.contact_info && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 truncate">
                          {truncate(conv.contact_info, 40)}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0 ml-4">
                    {conv.visitor_id && (
                      <span className="text-xs text-gray-400 font-mono">
                        {conv.visitor_id.slice(0, 12)}…
                      </span>
                    )}
                    <span className="text-xs text-gray-400 whitespace-nowrap">
                      {formatDate(conv.updated_at || conv.created_at)}
                    </span>
                    <DropdownMenu
                      trigger={
                        <button className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700">
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      }
                      items={[
                        {
                          label: t('conversations.openChat'),
                          onClick: () => navigate(`/chat/${conv.id}`),
                        },
                        {
                          label: t('conversations.closeConversation'),
                          onClick: () => {
                            api.post(`/chat/conversations/${conv.id}/close`).then(() => loadConversations())
                          },
                        },
                      ]}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog
        open={showCreate}
        onClose={() => { setShowCreate(false); setNewTitle('') }}
        title={t('conversations.dialogCreateTitle')}
      >
        <div className="space-y-4 pt-2">
          <Input
            label={t('conversations.titleLabel')}
            value={newTitle}
            onChange={(e: any) => setNewTitle(e.target.value)}
            placeholder={t('conversations.titlePlaceholder')}
            onKeyDown={(e: any) => e.key === 'Enter' && handleCreate()}
          />
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => { setShowCreate(false); setNewTitle('') }}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleCreate} isLoading={creating} disabled={!newTitle.trim()}>
              {t('common.create')}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
