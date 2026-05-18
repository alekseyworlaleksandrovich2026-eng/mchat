import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AgentConfig } from '@/components/admin/AgentConfig'
import { ModelProviderWorkbench } from '@/components/admin/ModelProviderWorkbench'
import { Tabs, TabPanel } from '@/components/ui/Tabs'

export function AgentsPage() {
  const { t } = useTranslation()
  const [tab, setTab] = useState('select')
  const tabs = [
    { id: 'select', label: t('agents.tabSelect') },
    { id: 'advanced', label: t('agents.tabAdvanced') },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {t('agents.pageTitle')}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t('agents.pageSubtitle')}
        </p>
      </div>
      <Tabs tabs={tabs} activeTab={tab} onChange={setTab} />
      <TabPanel id="select" activeTab={tab}>
        <ModelProviderWorkbench />
      </TabPanel>
      <TabPanel id="advanced" activeTab={tab}>
        <AgentConfig />
      </TabPanel>
    </div>
  )
}
