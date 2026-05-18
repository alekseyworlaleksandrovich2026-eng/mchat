import React from 'react'
import { useTranslation } from 'react-i18next'
import { SkillManager } from '@/components/admin/SkillManager'

export function SkillsPage() {
  const { t } = useTranslation()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {t('skills.pageTitle')}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t('skills.pageSubtitle')}
        </p>
      </div>

      <SkillManager />
    </div>
  )
}
