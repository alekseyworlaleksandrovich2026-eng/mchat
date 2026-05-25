import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

/** Collapsible "Advanced" block — keeps portal pages visually simple. */
export function PortalAdvancedPanel({
  children,
  defaultOpen = false,
  hint,
}: {
  children: ReactNode
  defaultOpen?: boolean
  hint?: string
}) {
  const { t } = useTranslation()

  return (
    <details
      open={defaultOpen}
      className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm group"
    >
      <summary className="cursor-pointer list-none px-6 py-4 text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center justify-between gap-2">
        <span>{t('portal.advancedSettings')}</span>
        <span className="text-xs text-gray-400 font-normal group-open:hidden shrink-0">
          {t('portal.expand')}
        </span>
      </summary>
      <div className="px-6 pb-6 border-t border-gray-100 dark:border-gray-700 pt-4 space-y-6">
        {hint && (
          <p className="text-sm text-gray-500 dark:text-gray-400">{hint}</p>
        )}
        {children}
      </div>
    </details>
  )
}

export function PortalAdvancedSubsection({
  title,
  hint,
  children,
}: {
  title: string
  hint?: string
  children: ReactNode
}) {
  return (
    <section className="space-y-3">
      <div>
        <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">{title}</h3>
        {hint && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{hint}</p>
        )}
      </div>
      {children}
    </section>
  )
}
