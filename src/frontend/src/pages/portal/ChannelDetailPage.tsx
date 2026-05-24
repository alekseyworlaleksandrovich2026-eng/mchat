import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, Check, Copy, ExternalLink, MessageSquare } from 'lucide-react'
import api from '@/lib/api'
import { portalApi, type MyChannel, type EmbedCode } from '@/lib/portalApi'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'

export function ChannelDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [channel, setChannel] = useState<MyChannel | null>(null)
  const [embed, setEmbed] = useState<EmbedCode | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [startingChat, setStartingChat] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({ name: '', welcome_message: '' })

  useEffect(() => {
    if (!id) return
    Promise.all([
      portalApi.getMyChannel(id),
      portalApi.getEmbedCode(id).catch(() => null),
    ]).then(([ch, em]) => {
      setChannel(ch)
      setEmbed(em)
      setForm({ name: ch.name, welcome_message: ch.welcome_message || '' })
    }).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }, [id])

  const handleSave = async () => {
    if (!id) return
    setSaving(true)
    try {
      const updated = await portalApi.updateMyChannel(id, form)
      setChannel(updated)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleCopy = () => {
    if (!embed?.embed_script) return
    navigator.clipboard.writeText(embed.embed_script).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const handleStartChat = async () => {
    setStartingChat(true)
    try {
      const conv = await api.post<{ id: string }>('/chat/conversations', {
        title: channel?.name || 'Chat',
      })
      navigate(`/chat/${conv.id}`)
    } catch (e: any) {
      setError(e.message || 'Failed to start chat')
    } finally {
      setStartingChat(false)
    }
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  if (!channel) return <div className="text-red-500 text-sm p-4">{error || 'Not found'}</div>

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/portal/channels')}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600 dark:text-gray-400">
        <ArrowLeft className="w-4 h-4" /> {t('portal.myChannels')}
      </button>

      {error && <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">{error}</div>}

      {/* Direct Chat */}
      <div className="bg-primary-50 dark:bg-primary-900/20 rounded-2xl border border-primary-200 dark:border-primary-800 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-primary-600 text-white flex items-center justify-center">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-gray-100">{channel.name}</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {channel.channel_category === 'patent_rag' ? 'Patent RAG' : channel.channel_category}
            </p>
          </div>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {channel.welcome_message || 'Start a conversation with this channel.'}
        </p>
        <Button onClick={handleStartChat} isLoading={startingChat} className="gap-2">
          <MessageSquare className="w-4 h-4" />
          {t('portal.startChat', 'Open Chat')}
        </Button>
      </div>

      {/* Usage */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Usage this month</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-gray-50 dark:bg-gray-900/50 rounded-xl">
            <p className="text-xs text-gray-500">Messages</p>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {(channel.usage_messages_month ?? 0).toLocaleString()}
              <span className="text-xs font-normal text-gray-400 ml-1">/ {(channel.usage_messages_limit ?? 0).toLocaleString()}</span>
            </p>
          </div>
          <div className="p-3 bg-gray-50 dark:bg-gray-900/50 rounded-xl">
            <p className="text-xs text-gray-500">Tokens</p>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {(channel.usage_tokens_month ?? 0) >= 1000 ? `${((channel.usage_tokens_month ?? 0) / 1000).toFixed(1)}k` : (channel.usage_tokens_month ?? 0)}
              <span className="text-xs font-normal text-gray-400 ml-1">/ {((channel.usage_tokens_limit ?? 0) >= 1000 ? `${((channel.usage_tokens_limit ?? 0) / 1000).toFixed(0)}k` : (channel.usage_tokens_limit ?? 0))}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">{t('portal.channelSettings')}</h2>
        <div className="space-y-4">
          <Input label={t('common.name')} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="Welcome message" value={form.welcome_message} onChange={(e) => setForm({ ...form, welcome_message: e.target.value })} />
          <Button onClick={handleSave} isLoading={saving}>{t('common.save')}</Button>
        </div>
      </div>

      {/* Embed */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">{t('portal.embedCode')}</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">{t('portal.embedHint')}</p>
        {embed && (
          <>
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto mb-3">{embed.embed_script}</pre>
            <div className="flex items-center gap-3">
              <Button onClick={handleCopy} size="sm" className="gap-1">
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {copied ? t('portal.copied') : t('portal.copyCode')}
              </Button>
              <a href={embed.widget_url} target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:underline">
                {t('common.preview')} <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
