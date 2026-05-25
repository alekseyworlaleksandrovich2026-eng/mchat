import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, FileText, Printer } from 'lucide-react'
import { portalApi, type PortalInvoice, type PortalOrderDetail } from '@/lib/portalApi'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'

function fmtDate(iso: string | null | undefined) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function InvoiceBlock({ inv }: { inv: PortalInvoice }) {
  const { t } = useTranslation()
  return (
    <div
      id="mchat-invoice-print"
      className="rounded-xl border border-gray-200 dark:border-gray-700 p-6 bg-white dark:bg-gray-800 text-sm space-y-4"
    >
      <div className="text-center border-b border-gray-100 dark:border-gray-700 pb-4">
        <h2 className="text-lg font-bold">{inv.company_name}</h2>
        {inv.company_tax_id && (
          <p className="text-gray-500 text-xs mt-1">
            {t('portal.invoiceTaxId')}: {inv.company_tax_id}
          </p>
        )}
        <p className="text-base font-semibold mt-3">{t('portal.invoiceTitle')}</p>
      </div>
      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <dt className="text-gray-500 dark:text-gray-400">{t('portal.orderNo')}</dt>
          <dd className="font-mono text-gray-900 dark:text-gray-200">{inv.order_no}</dd>
        </div>
        <div>
          <dt className="text-gray-500">{t('portal.orderPaidAt')}</dt>
          <dd>{fmtDate(inv.paid_at)}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-gray-500">{t('portal.orderSubject')}</dt>
          <dd>{inv.subject}</dd>
        </div>
        {inv.template_name && (
          <div>
            <dt className="text-gray-500">{t('portal.templateLabel')}</dt>
            <dd>{inv.template_name}</dd>
          </div>
        )}
        {inv.channel_name && (
          <div>
            <dt className="text-gray-500">{t('portal.assistantLabel')}</dt>
            <dd>{inv.channel_name}</dd>
          </div>
        )}
        <div>
          <dt className="text-gray-500">{t('portal.billingPeriod')}</dt>
          <dd>{inv.billing_period === 'yearly' ? t('portal.yearly') : t('portal.monthly')}</dd>
        </div>
        <div>
          <dt className="text-gray-500">{t('portal.orderAmount')}</dt>
          <dd className="font-semibold">¥{inv.amount_yuan}</dd>
        </div>
        {inv.payment_method && (
          <div>
            <dt className="text-gray-500">{t('portal.paymentMethod')}</dt>
            <dd>{inv.payment_method}</dd>
          </div>
        )}
        {inv.provider_trade_no && (
          <div>
            <dt className="text-gray-500">{t('portal.tradeNo')}</dt>
            <dd className="font-mono text-xs break-all">{inv.provider_trade_no}</dd>
          </div>
        )}
        {inv.subscription_ends_at && (
          <div>
            <dt className="text-gray-500">{t('portal.subscriptionEnds')}</dt>
            <dd>{fmtDate(inv.subscription_ends_at)}</dd>
          </div>
        )}
        {(inv.buyer_email || inv.buyer_phone) && (
          <div className="sm:col-span-2 border-t border-gray-100 dark:border-gray-700 pt-3">
            <dt className="text-gray-500 mb-1">{t('portal.invoiceBuyer')}</dt>
            <dd>
              {inv.buyer_email && <span className="block">{inv.buyer_email}</span>}
              {inv.buyer_phone && <span className="block">{inv.buyer_phone}</span>}
            </dd>
          </div>
        )}
      </dl>
      {inv.support_email && (
        <p className="text-xs text-gray-400 text-center pt-2">
          {t('portal.invoiceSupport')}: {inv.support_email}
        </p>
      )}
    </div>
  )
}

export function OrderDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const [order, setOrder] = useState<PortalOrderDetail | null>(null)
  const [invoice, setInvoice] = useState<PortalInvoice | null>(null)
  const [loading, setLoading] = useState(true)
  const [invoiceLoading, setInvoiceLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const loadedInvoice = useRef(false)

  useEffect(() => {
    if (!id) return
    portalApi
      .getOrder(id)
      .then(setOrder)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  const loadInvoice = () => {
    if (!id || loadedInvoice.current) return
    setInvoiceLoading(true)
    portalApi
      .getOrderInvoice(id)
      .then((inv) => {
        setInvoice(inv)
        loadedInvoice.current = true
      })
      .catch((e) => setError(e.message))
      .finally(() => setInvoiceLoading(false))
  }

  const handlePrint = () => {
    if (!invoice) {
      loadInvoice()
      setTimeout(() => window.print(), 500)
      return
    }
    window.print()
  }

  useEffect(() => {
    if (order?.status === 'paid' && !loadedInvoice.current) {
      loadInvoice()
    }
  }, [order?.status])

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!order) {
    return <p className="text-sm text-gray-500">{error || t('portal.orderNotFound')}</p>
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <Link
        to="/portal/orders"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="w-4 h-4" />
        {t('portal.backToOrders')}
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {t('portal.orderDetailTitle')}
          </h1>
          <p className="font-mono text-sm text-gray-500 mt-1">{order.order_no}</p>
        </div>
        {order.status === 'paid' && (
          <Button size="sm" variant="outline" className="gap-1" onClick={handlePrint}>
            <Printer className="w-4 h-4" />
            {t('portal.printInvoice')}
          </Button>
        )}
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 text-sm text-red-600 border border-red-200">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-gray-900 dark:text-gray-200">
          <div>
            <dt className="text-gray-500 dark:text-gray-400">{t('portal.orderSubject')}</dt>
            <dd className="font-medium text-gray-900 dark:text-gray-100">{order.subject}</dd>
          </div>
          <div>
            <dt className="text-gray-500">{t('portal.orderStatus')}</dt>
            <dd>{order.status}</dd>
          </div>
          <div>
            <dt className="text-gray-500">{t('portal.orderAmount')}</dt>
            <dd>¥{(order.amount_cents / 100).toFixed(2)}</dd>
          </div>
          <div>
            <dt className="text-gray-500">{t('portal.billingPeriod')}</dt>
            <dd>
              {order.billing_period === 'yearly' ? t('portal.yearly') : t('portal.monthly')}
              {order.is_renewal && (
                <span className="ml-2 text-xs text-primary-600">({t('portal.renewal')})</span>
              )}
            </dd>
          </div>
          {order.template_name && (
            <div>
              <dt className="text-gray-500">{t('portal.templateLabel')}</dt>
              <dd>{order.template_name}</dd>
            </div>
          )}
          <div>
            <dt className="text-gray-500">{t('portal.orderPaidAt')}</dt>
            <dd>{fmtDate(order.paid_at)}</dd>
          </div>
          <div>
            <dt className="text-gray-500">{t('portal.subscriptionEnds')}</dt>
            <dd>{fmtDate(order.subscription_ends_at)}</dd>
          </div>
          <div>
            <dt className="text-gray-500">{t('portal.orderCreated')}</dt>
            <dd>{fmtDate(order.created_at)}</dd>
          </div>
        </dl>
        {order.channel_id && (
          <Link
            to={`/portal/channels/${order.channel_id}`}
            className="inline-block mt-4 text-sm text-primary-600 hover:underline"
          >
            {t('portal.openAssistant')}
          </Link>
        )}
      </div>

      {order.status === 'paid' && (
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            {t('portal.invoiceSection')}
          </h2>
          {invoiceLoading && !invoice ? (
            <Spinner />
          ) : invoice ? (
            <InvoiceBlock inv={invoice} />
          ) : (
            <Button size="sm" onClick={loadInvoice}>
              {t('portal.loadInvoice')}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
