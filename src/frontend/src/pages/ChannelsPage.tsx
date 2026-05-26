import React, { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Globe,
  Plus,
  CheckCircle,
  XCircle,
  Zap,
  Settings2,
  Trash2,
} from 'lucide-react'
import { getChannelTypes } from '@/i18n/channelTypes'
import api from '@/lib/api'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Switch } from '@/components/ui/Switch'
import { Badge } from '@/components/ui/Badge'
import { Dialog } from '@/components/ui/Dialog'
import { toast } from '@/components/ui/Toast'
import { Spinner } from '@/components/ui/Spinner'
import { formatDate } from '@/lib/utils'

interface Channel {
  id: string
  user_id: string
  name: string
  channel_type: string
  config: Record<string, any> | null
  enabled: boolean
  is_connected: boolean
  created_at: string
  updated_at: string
}

interface CustomerConfigOption {
  id: string
  name: string
}

export function ChannelsPage() {
  const { t, i18n } = useTranslation()
  const CHANNEL_TYPES = useMemo(() => getChannelTypes(t), [t, i18n.language])
  const [channels, setChannels] = useState<Channel[]>([])
  const [customerConfigs, setCustomerConfigs] = useState<CustomerConfigOption[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editingChannel, setEditingChannel] = useState<Channel | null>(null)
  const [saving, setSaving] = useState(false)
  const [newChannel, setNewChannel] = useState({
    name: '',
    channel_type: 'web_widget',
    config: {} as Record<string, any>,
    enabled: false,
  })
  const [editConfig, setEditConfig] = useState<Record<string, any>>({})
  const [editName, setEditName] = useState('')
  const [editEnabled, setEditEnabled] = useState(false)
  const [webhookInfo, setWebhookInfo] = useState<{
    webhook_url: string
    hint: string
  } | null>(null)

  useEffect(() => {
    loadChannels()
    loadCustomerConfigs()
  }, [])

  const loadCustomerConfigs = async () => {
    try {
      const data = await api.get<CustomerConfigOption[]>('/agents/customer-configs')
      setCustomerConfigs(data)
    } catch {
      /* optional */
    }
  }

  const loadChannels = async () => {
    try {
      const data = await api.get<Channel[]>('/channels')
      setChannels(data)
    } catch (err) {
      console.error('Failed to load channels:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!newChannel.name.trim()) return
    setSaving(true)
    try {
      const created = await api.post<Channel>('/channels', {
        name: newChannel.name,
        channel_type: newChannel.channel_type,
        config: newChannel.config,
        enabled: newChannel.enabled,
      })
      setChannels((prev) => [...prev, created])
      setCreateOpen(false)
      setNewChannel({ name: '', channel_type: 'web_widget', config: {}, enabled: false })
      toast(t('channels.toastCreated'), { type: 'success' })
    } catch (err: any) {
      toast(t('channels.toastCreateFailed'), { type: 'error', message: err.message })
    } finally {
      setSaving(false)
    }
  }

  const openEdit = async (ch: Channel) => {
    setEditingChannel(ch)
    setEditConfig(ch.config || {})
    setEditName(ch.name)
    setEditEnabled(ch.enabled)
    setWebhookInfo(null)
    setEditOpen(true)
    const webhookTypes = new Set([
      'wechat',
      'telegram',
      'dingtalk',
      'whatsapp',
      'slack',
      'line',
      'custom',
    ])
    if (webhookTypes.has(ch.channel_type)) {
      try {
        const info = await api.get<{ webhook_url: string; hint: string }>(
          `/channels/${ch.id}/webhook-info`,
        )
        if (info.webhook_url) setWebhookInfo(info)
      } catch {
        /* optional */
      }
    }
  }

  const handleUpdate = async () => {
    if (!editingChannel) return
    setSaving(true)
    try {
      await api.put(`/channels/${editingChannel.id}`, {
        name: editName,
        config: editConfig,
        enabled: editEnabled,
      })
      setChannels((prev) =>
        prev.map((c) =>
          c.id === editingChannel.id
            ? { ...c, name: editName, config: editConfig, enabled: editEnabled }
            : c,
        ),
      )
      setEditOpen(false)
      toast(t('channels.toastUpdated'), { type: 'success' })
    } catch (err: any) {
      toast(t('channels.toastUpdateFailed'), { type: 'error', message: err.message })
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      await api.put(`/channels/${id}`, { enabled })
      setChannels((prev) =>
        prev.map((c) => (c.id === id ? { ...c, enabled } : c)),
      )
    } catch (err: any) {
      toast(t('channels.toastOpFailed'), { type: 'error', message: err.message })
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/channels/${id}`)
      setChannels((prev) => prev.filter((c) => c.id !== id))
      toast(t('channels.toastDeleted'), { type: 'success' })
    } catch (err: any) {
      toast(t('channels.toastDeleteFailed'), { type: 'error', message: err.message })
    }
  }

  const handleTest = async (ch: Channel) => {
    try {
      const result = await api.post<{
        ok: boolean
        message: string
        preview_url?: string
      }>('/channels/test', {
        channel_type: ch.channel_type,
        config: ch.config || {},
      })
      if (result.ok) {
        toast(result.message, { type: 'success' })
        if (ch.channel_type === 'web_widget' && result.preview_url) {
          window.open(result.preview_url, '_blank', 'noopener,noreferrer')
        }
      } else {
        toast(result.message, { type: 'error' })
      }
    } catch (err: any) {
      toast(t('channels.toastTestFailed'), { type: 'error', message: err.message })
    }
  }

  const renderConfigField = (
    field: { key: string; label: string; placeholder: string; type?: string },
    config: Record<string, string>,
    onChange: (key: string, value: string) => void,
    channelType: string,
  ) => {
    if (
      (channelType === 'web_widget' && field.key === 'widget_id') ||
      (channelType === 'wechat' && field.key === 'customer_id')
    ) {
      const valueKey = channelType === 'wechat' ? 'customer_id' : 'widget_id'
      return (
        <div key={field.key} className="space-y-1">
          <Select
            label={field.label}
            options={[
              { value: '', label: t('channels.selectCustomerConfig') },
              ...customerConfigs.map((c) => ({
                value: c.id,
                label: `${c.name} (${c.id.slice(0, 8)}…)`,
              })),
            ]}
            value={config[valueKey] || ''}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
              onChange(valueKey, e.target.value)
            }
          />
          {channelType === 'web_widget' && (
            <p className="text-xs text-gray-500">
              {t('channels.widgetTestHint')}{' '}
              <a href="/widget/demo" className="text-primary-600 hover:underline" target="_blank" rel="noreferrer">
                {t('channels.widgetDemoLink')}
              </a>
            </p>
          )}
          {channelType === 'wechat' && (
            <p className="text-xs text-gray-500">
              {t('channels.wechatAgentHint')}
            </p>
          )}
        </div>
      )
    }
    return (
      <Input
        key={field.key}
        label={field.label}
        type={field.type || 'text'}
        value={config[field.key] || ''}
        onChange={(e) => onChange(field.key, e.target.value)}
        placeholder={field.placeholder}
      />
    )
  }

  const selectedType = newChannel.channel_type
  const typeFields = CHANNEL_TYPES[selectedType]?.fields || []

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('channels.pageTitle')}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t('channels.pageSubtitle')}
          </p>
        </div>
        <Button
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => setCreateOpen(true)}
        >
          {t('channels.addChannel')}
        </Button>
      </div>

      {channels.length === 0 ? (
        <Card>
          <CardContent>
            <div className="flex flex-col items-center py-16 text-gray-400">
              <Globe className="w-16 h-16 mb-4 opacity-30" />
              <p className="text-base font-medium mb-1">{t('channels.emptyTitle')}</p>
              <p className="text-sm mb-4">{t('channels.emptyHint')}</p>
              <Button onClick={() => setCreateOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
                {t('channels.addFirst')}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {channels.map((ch) => {
            const typeInfo = CHANNEL_TYPES[ch.channel_type] || CHANNEL_TYPES.custom
            const Icon = typeInfo.icon
            return (
              <Card key={ch.id} hover>
                <CardContent className="py-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                        ch.enabled
                          ? 'bg-green-50 dark:bg-green-900/20'
                          : 'bg-gray-100 dark:bg-gray-700'
                      }`}>
                        <Icon className={`w-5 h-5 ${
                          ch.enabled ? 'text-green-600 dark:text-green-400' : 'text-gray-400'
                        }`} />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-gray-100">{ch.name}</h3>
                        <p className="text-xs text-gray-500">{typeInfo.label}</p>
                      </div>
                    </div>
                    <Switch
                      checked={ch.enabled}
                      onChange={(checked) => handleToggle(ch.id, checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      {ch.enabled ? (
                        <Badge variant="success" size="sm">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          {t('common.enabled')}
                        </Badge>
                      ) : (
                        <Badge variant="default" size="sm">
                          <XCircle className="w-3 h-3 mr-1" />
                          {t('common.disabled')}
                        </Badge>
                      )}
                      <span>{formatDate(ch.created_at)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleTest(ch)}
                        className="p-1.5 rounded text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
                        title={t('channels.testConnection')}
                      >
                        <Zap className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => openEdit(ch)}
                        className="p-1.5 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                        title={t('common.configure')}
                      >
                        <Settings2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(ch.id)}
                        className="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                        title={t('common.delete')}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title={t('channels.dialogAdd')}
        size="md"
      >
        <div className="space-y-4">
          <Select
            label={t('channels.channelType')}
            options={Object.entries(CHANNEL_TYPES).map(([k, v]) => ({ value: k, label: v.label }))}
            value={selectedType}
            onChange={(e: any) => {
              setNewChannel({ ...newChannel, channel_type: e.target.value, config: {} })
            }}
          />
          <Input
            label={t('channels.channelName')}
            value={newChannel.name}
            onChange={(e) => setNewChannel({ ...newChannel, name: e.target.value })}
            placeholder={t('channels.channelNamePlaceholder')}
          />
          <p className="text-xs text-gray-500">{CHANNEL_TYPES[selectedType]?.description}</p>
          {typeFields.map((field) =>
            renderConfigField(
              field,
              newChannel.config,
              (key, value) =>
                setNewChannel({
                  ...newChannel,
                  config: { ...newChannel.config, [key]: value },
                }),
              selectedType,
            ),
          )}
          {selectedType === 'wechat' && (
            <p className="text-xs text-amber-600 dark:text-amber-400">
              {t('channels.wechatActivePushHint')}
            </p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleCreate} isLoading={saving} disabled={!newChannel.name.trim()}>
              {t('common.create')}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog
        open={editOpen}
        onClose={() => setEditOpen(false)}
        title={t('channels.dialogEdit')}
        size="md"
      >
        {editingChannel && (
          <div className="space-y-4">
            <Input
              label={t('channels.channelName')}
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
            />
            <p className="text-xs text-gray-500">
              {t('channels.typeLabel')}: {CHANNEL_TYPES[editingChannel.channel_type]?.label || editingChannel.channel_type}
            </p>
            {(CHANNEL_TYPES[editingChannel.channel_type]?.fields || []).map((field) =>
              renderConfigField(
                field,
                editConfig,
                (key, value) => setEditConfig({ ...editConfig, [key]: value }),
                editingChannel.channel_type,
              ),
            )}
            {editingChannel.channel_type === 'wechat' && (
              <p className="text-xs text-amber-600 dark:text-amber-400">
                {t('channels.wechatActivePushHint')}
              </p>
            )}
            {webhookInfo && (
              <div className="rounded-lg bg-gray-50 dark:bg-gray-900 p-3 space-y-2 text-xs">
                <p className="font-medium text-gray-700 dark:text-gray-300">{t('channels.webhookUrlLabel')}</p>
                <code className="block break-all text-primary-700 dark:text-primary-400">
                  {webhookInfo.webhook_url}
                </code>
                <p className="text-gray-500">{webhookInfo.hint}</p>
              </div>
            )}
            <div className="flex items-center justify-between pt-2">
              <span className="text-sm text-gray-700 dark:text-gray-300">{t('channels.enable')}</span>
              <Switch checked={editEnabled} onChange={setEditEnabled} />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setEditOpen(false)}>
                {t('common.cancel')}
              </Button>
              <Button onClick={handleUpdate} isLoading={saving}>
                {t('common.save')}
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  )
}
