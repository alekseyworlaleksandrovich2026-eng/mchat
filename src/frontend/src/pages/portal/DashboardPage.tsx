import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { LayoutDashboard, MessageSquare, ShoppingBag, Zap, TrendingUp } from 'lucide-react'
import { portalApi, type PortalDashboardStats } from '@/lib/portalApi'
import { Spinner } from '@/components/ui/Spinner'
import { useAuthStore } from '@/stores/auth'

const formatTokens = (n: number) => n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)

export function DashboardPage() {
  const { t } = useTranslation()
  const { user } = useAuthStore()
  const [stats, setStats] = useState<PortalDashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    portalApi.getDashboardStats().then(setStats).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  if (error) return <div className="text-red-500 text-sm p-4">{error}</div>

  const statCards = [
    { label: t('portal.myChannels'), v: stats?.total_channels ?? 0, icon: MessageSquare },
    { label: 'Active', v: stats?.active_channels ?? 0, icon: Zap },
    { label: 'Conversations', v: stats?.total_conversations ?? 0, icon: LayoutDashboard },
    { label: 'Today', v: stats?.messages_today ?? 0, icon: MessageSquare },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('portal.dashboard')}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">{user?.display_name || user?.username}</p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((c) => (
          <div key={c.label} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 shadow-sm">
            <div className="flex items-center gap-2 text-gray-400 mb-2">
              <c.icon className="w-4 h-4" /><span className="text-xs uppercase tracking-wide">{c.label}</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{c.v}</p>
          </div>
        ))}
      </div>

      {/* Usage overview */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          <TrendingUp className="w-5 h-5 inline mr-2" />Usage this month
        </h2>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <p className="text-xs text-gray-500 mb-1">Messages</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{(stats?.total_messages_month ?? 0).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Tokens</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{formatTokens(stats?.total_tokens_month ?? 0)}</p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Quick actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link to="/portal/templates" className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm">
            <ShoppingBag className="w-4 h-4" />{t('portal.browseTemplates')}
          </Link>
          <Link to="/portal/channels" className="inline-flex items-center gap-2 px-4 py-2 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm">
            <MessageSquare className="w-4 h-4" />{t('portal.myChannels')}
          </Link>
        </div>
      </div>
    </div>
  )
}
