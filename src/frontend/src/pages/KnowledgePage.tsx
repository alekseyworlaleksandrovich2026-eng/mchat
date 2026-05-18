import React from 'react'
import { useTranslation } from 'react-i18next'
import { KnowledgeManager } from '@/components/admin/KnowledgeManager'

export function KnowledgePage() {
  const { t } = useTranslation()

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {t('knowledge.pageTitle')}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t('knowledge.pageSubtitle')}
        </p>
      </div>

      <div className="flex-1 min-h-0">
        <KnowledgeManager />
      </div>
    </div>
  )
}
