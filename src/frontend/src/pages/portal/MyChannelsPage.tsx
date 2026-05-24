import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ExternalLink, MessageSquare, ShoppingBag, Trash2 } from 'lucide-react'
import { portalApi, type MyChannel } from '@/lib/portalApi'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'

export function MyChannelsPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [channels, setChannels] = useState<MyChannel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    portalApi.getMyChannels().then(setChannels).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const handleDelete = async (id: string) => {
    if (!confirm(t('portal.deleteConfirm'))) return
    try {
      await portalApi.deleteMyChannel(id)
      setChannels((prev) => prev.filter((c) => c.id !== id))
    } catch (e: any) {
      setError(e.message)
    }
  }

  const planBadge = (plan: string) => {
    const map: Record<string, string> = { free: t('portal.planFree'), free_trial: t('portal.planFreeTrial'), pro: t('portal.planPro'), enterprise: t('portal.planEnterprise') }
    return map[plan] || plan
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('portal.myChannels')}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">{channels.length} channels</p>
        </div>
        <Button onClick={() => navigate('/portal/templates')} size="sm">
          <ShoppingBag className="w-4 h-4 mr-1" />{t('portal.browseTemplates')}
        </Button>
      </div>

      {error && <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">{error}</div>}

      {channels.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-40" />
          <p className="font-medium">{t('portal.noChannels')}</p>
          <p className="text-sm mt-1">{t('portal.noChannelsHint')}</p>
          <Link to="/portal/templates" className="inline-flex items-center gap-2 mt-4 text-sm font-medium text-primary-600 dark:text-primary-400">
            <ShoppingBag className="w-4 h-4" />{t('portal.browseTemplates')}
          </Link>
        </div>
      )}

      <div className="space-y-3">
        {channels.map((channel) => (
          <div key={channel.id}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 shadow-sm flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{channel.name}</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  channel.plan === 'free' ? 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400' :
                  channel.plan === 'free_trial' ? 'bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400' :
                  'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                }`}>{planBadge(channel.plan)}</span>
                {!channel.enabled && <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 dark:bg-red-900/30 text-red-600">{t('common.disabled')}</span>}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{channel.channel_category}</p>
              {channel.trial_ends_at && (
                <p className="text-xs text-gray-400 mt-0.5">{t('portal.trialRemaining', { days: Math.max(0, Math.ceil((new Date(channel.trial_ends_at).getTime() - Date.now()) / 86400000)) })}</p>
              )}
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button onClick={() => navigate(`/portal/channels/${channel.id}`)}
                className="p-2 text-gray-500 hover:text-primary-600 dark:hover:text-primary-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title={t('common.edit')}>
                <ExternalLink className="w-4 h-4" />
              </button>
              <button onClick={() => handleDelete(channel.id)}
                className="p-2 text-gray-500 hover:text-red-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title={t('common.delete')}>
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
