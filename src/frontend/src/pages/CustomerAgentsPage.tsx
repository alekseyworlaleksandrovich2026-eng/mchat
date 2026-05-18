import React from 'react'
import { useTranslation } from 'react-i18next'
import { CustomerConfig } from '@/components/admin/CustomerConfig'

export function CustomerAgentsPage() {
  const { t } = useTranslation()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {t('customerAgents.pageTitle')}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t('customerAgents.pageSubtitle')}
        </p>
      </div>
      <CustomerConfig />
    </div>
  )
}
