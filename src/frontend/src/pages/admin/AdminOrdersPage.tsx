import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '@/lib/api'
import { Spinner } from '@/components/ui/Spinner'

interface AdminOrder {
  id: string
  order_no: string
  subject: string
  status: string
  amount_cents: number
  billing_period: string
  payment_method: string | null
  channel_id: string | null
  user_username: string | null
  user_phone: string | null
  paid_at: string | null
  created_at: string
}

interface RevenueStats {
  paid_order_count: number
  total_revenue_cents: number
  month_revenue_cents: number
  pending_order_count: number
}

function fmtDate(iso: string | null | undefined) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

export function AdminOrdersPage() {
  const { t } = useTranslation()
  const [orders, setOrders] = useState<AdminOrder[]>([])
  const [stats, setStats] = useState<RevenueStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api.get<AdminOrder[]>('/admin/orders'),
      api.get<RevenueStats>('/admin/orders/revenue'),
    ])
      .then(([o, s]) => {
        setOrders(o)
        setStats(s)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6 text-gray-900 dark:text-gray-200">
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
          {t('adminOrders.title')}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t('adminOrders.subtitle')}
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 text-sm text-red-600 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label={t('adminOrders.totalRevenue')}
            value={`¥${(stats.total_revenue_cents / 100).toFixed(2)}`}
          />
          <StatCard
            label={t('adminOrders.monthRevenue')}
            value={`¥${(stats.month_revenue_cents / 100).toFixed(2)}`}
          />
          <StatCard
            label={t('adminOrders.paidCount')}
            value={String(stats.paid_order_count)}
          />
          <StatCard
            label={t('adminOrders.pendingCount')}
            value={String(stats.pending_order_count)}
          />
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-900/50 text-left text-gray-500 dark:text-gray-400">
            <tr>
              <th className="px-4 py-3">{t('portal.orderNo')}</th>
              <th className="px-4 py-3">{t('portal.orderSubject')}</th>
              <th className="px-4 py-3">{t('adminOrders.buyer')}</th>
              <th className="px-4 py-3">{t('portal.orderAmount')}</th>
              <th className="px-4 py-3">{t('portal.orderStatus')}</th>
              <th className="px-4 py-3">{t('portal.orderPaidAt')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-gray-900 dark:text-gray-200">
            {orders.map((o) => (
              <tr key={o.id}>
                <td className="px-4 py-3 font-mono text-xs text-gray-800 dark:text-gray-200">
                  {o.order_no}
                </td>
                <td className="px-4 py-3">{o.subject}</td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                  {o.user_phone || o.user_username || '—'}
                </td>
                <td className="px-4 py-3">¥{(o.amount_cents / 100).toFixed(2)}</td>
                <td className="px-4 py-3">{o.status}</td>
                <td className="px-4 py-3">{fmtDate(o.paid_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
      <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
      <p className="text-xl font-bold text-gray-900 dark:text-gray-100 mt-1">{value}</p>
    </div>
  )
}
