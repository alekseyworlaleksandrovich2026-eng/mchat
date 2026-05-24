import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, FileSearch, MessageSquare } from 'lucide-react'
import { portalApi, type ChannelTemplate } from '@/lib/portalApi'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = { FileSearch, MessageSquare }

export function TemplateDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [template, setTemplate] = useState<ChannelTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [renting, setRenting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    portalApi.getTemplate(id).then(setTemplate).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }, [id])

  const handleRent = async () => {
    if (!id) return
    setRenting(true)
    try {
      await portalApi.rentChannel(id)
      navigate('/portal/channels', { replace: true })
    } catch (e: any) {
      setError(e.message || t('portal.rentFailed'))
    } finally {
      setRenting(false)
    }
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  if (!template) return <div className="text-red-500 text-sm p-4">{error || t('common.noData')}</div>

  const Icon = iconMap[template.icon || ''] || MessageSquare
  const price = template.price_monthly_cents > 0
    ? `¥${(template.price_monthly_cents / 100).toFixed(0)}${t('portal.monthly')}`
    : t('portal.planFree')

  return (
    <div className="space-y-6 max-w-2xl">
      <button onClick={() => navigate('/portal/templates')}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600 dark:text-gray-400">
        <ArrowLeft className="w-4 h-4" /> {t('portal.templates')}
      </button>

      {error && <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">{error}</div>}

      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-14 h-14 rounded-2xl bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 flex items-center justify-center shrink-0">
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{template.name}</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{template.description}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl">
          <div>
            <p className="text-xs text-gray-500">{t('portal.monthly')}</p>
            <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{price}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">{t('portal.trialDays', { days: template.trial_days })}</p>
            <p className="text-sm text-green-600 dark:text-green-400 font-medium">
              {template.trial_days > 0 ? t('portal.trialRemaining', { days: template.trial_days }) : t('portal.noTrial')}
            </p>
          </div>
        </div>

        <Button onClick={handleRent} className="w-full" size="lg" isLoading={renting}>
          {template.trial_days > 0 ? t('portal.rentChannel') : t('portal.rentChannel')}
        </Button>
      </div>
    </div>
  )
}
