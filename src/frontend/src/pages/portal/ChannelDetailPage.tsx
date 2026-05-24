import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, Check, Copy, ExternalLink } from 'lucide-react'
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

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  if (!channel) return <div className="text-red-500 text-sm p-4">{error || 'Not found'}</div>

  return (
    <div className="space-y-6 max-w-2xl">
      <button onClick={() => navigate('/portal/channels')}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600 dark:text-gray-400">
        <ArrowLeft className="w-4 h-4" /> {t('portal.myChannels')}
      </button>

      {error && <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">{error}</div>}

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
