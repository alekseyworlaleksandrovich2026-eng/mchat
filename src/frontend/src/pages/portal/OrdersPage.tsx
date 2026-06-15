import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { portalApi, type PortalOrder } from '@/lib/portalApi'
import { Spinner } from '@/components/ui/Spinner'

function fmtDate(iso: string | null | undefined) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

export function OrdersPage() {
  const { t } = useTranslation()
  const [orders, setOrders] = useState<PortalOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    portalApi
      .getOrders()
      .then(setOrders)
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
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
          {t('portal.ordersTitle')}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t('portal.ordersSubtitle')}
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 text-sm text-red-600 border border-red-200">
          {error}
        </div>
      )}

      {orders.length === 0 ? (
        <p className="text-sm text-gray-500">{t('portal.noOrders')}</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900/50 text-left text-gray-500">
              <tr>
                <th className="px-4 py-3">{t('portal.orderNo')}</th>
                <th className="px-4 py-3">{t('portal.orderSubject')}</th>
                <th className="px-4 py-3">{t('portal.orderAmount')}</th>
                <th className="px-4 py-3">{t('portal.orderStatus')}</th>
                <th className="px-4 py-3">{t('portal.subscriptionEnds')}</th>
                <th className="px-4 py-3">{t('portal.orderPaidAt')}</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-gray-900 dark:text-gray-200">
              {orders.map((o) => (
                <tr key={o.id}>
                  <td className="px-4 py-3 font-mono text-xs text-gray-800 dark:text-gray-200">
                    {o.order_no}
                  </td>
                  <td className="px-4 py-3">
                    {o.subject}
                    {o.channel_id && (
                      <Link
                        to={`/portal/channels/${o.channel_id}`}
                        className="block text-xs text-primary-600 dark:text-primary-400 mt-1"
                      >
                        {t('portal.openAssistant')}
                      </Link>
                    )}
                  </td>
                  <td className="px-4 py-3">¥{(o.amount_cents / 100).toFixed(2)}</td>
                  <td className="px-4 py-3">{o.status}</td>
                  <td className="px-4 py-3">{fmtDate(o.subscription_ends_at)}</td>
                  <td className="px-4 py-3">{fmtDate(o.paid_at)}</td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/portal/orders/${o.id}`}
                      className="text-primary-600 dark:text-primary-400 hover:underline text-xs"
                    >
                      {t('portal.orderDetail')}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
