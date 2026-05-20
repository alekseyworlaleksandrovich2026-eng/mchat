import React, { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  MessageCircle,
  Copy,
  ExternalLink,
  Play,
  RefreshCw,
} from 'lucide-react'
import api, { getToken } from '@/lib/api'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Tabs, TabPanel } from '@/components/ui/Tabs'
import { Widget } from '@/components/widget/Widget'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { toast } from '@/components/ui/Toast'
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher'

interface CustomerOption {
  id: string
  name: string
  enabled: boolean
}

export function WidgetDemo() {
  const { t } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState('preview')
  const [agentId, setAgentId] = useState(searchParams.get('agentId') || '')
  const [customerConfigs, setCustomerConfigs] = useState<CustomerOption[]>([])
  const [widgetKey, setWidgetKey] = useState(0)
  const [previewPosition, setPreviewPosition] = useState<'right' | 'left'>('right')
  const [previewColor, setPreviewColor] = useState('#3b82f6')
  const [previewLauncherIcon, setPreviewLauncherIcon] = useState('chat')
  const [previewLauncherText, setPreviewLauncherText] = useState('')

  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  const apiBase = `${origin}/api`

  useEffect(() => {
    if (getToken()) {
      api
        .get<CustomerOption[]>('/agents/customer-configs')
        .then(setCustomerConfigs)
        .catch(() => {})
    }
  }, [])

  useEffect(() => {
    const id = searchParams.get('agentId')
    if (id) setAgentId(id)
  }, [searchParams])

  const applyAgentId = (id: string) => {
    setAgentId(id.trim())
    if (id.trim()) {
      setSearchParams({ agentId: id.trim() })
    } else {
      setSearchParams({})
    }
    setWidgetKey((k) => k + 1)
  }

  const embedScript = useMemo(() => {
    if (!agentId) return ''
    return `<!-- MChat Widget -->
<script
  src="${origin}/widget-loader.js?v=8"
  data-mchat-url="${apiBase}"
  data-agent-id="${agentId}"
  data-position="${previewPosition}"
  data-primary-color="${previewColor}"
  data-welcome-message="${t('widgetDemo.embedWelcome')}"
  data-bot-name="${t('widgetDemo.embedBotName')}"
  data-launcher-icon="${previewLauncherIcon}"
  data-launcher-text="${previewLauncherText.replace(/"/g, '&quot;')}"
></script>`
  }, [agentId, origin, apiBase, previewPosition, previewColor, previewLauncherIcon, previewLauncherText, t])

  const copyEmbed = async () => {
    if (!embedScript) {
      toast(t('widgetDemo.toastNeedAgent'), { type: 'error' })
      return
    }
    try {
      await navigator.clipboard.writeText(embedScript)
      toast(t('widgetDemo.toastCopied'), { type: 'success' })
    } catch {
      toast(t('widgetDemo.toastCopyFailed'), { type: 'error' })
    }
  }

  const openStandalone = () => {
    if (!agentId) {
      toast(t('widgetDemo.toastNeedAgent'), { type: 'error' })
      return
    }
    window.open(`/widget?agentId=${encodeURIComponent(agentId)}`, '_blank')
  }

  const openIframePage = () => {
    if (!agentId) {
      toast(t('widgetDemo.toastNeedAgent'), { type: 'error' })
      return
    }
    window.open(`/widget.html?agentId=${encodeURIComponent(agentId)}`, '_blank')
  }

  const tabs = [
    { id: 'preview', label: t('widgetDemo.tabPreview') },
    { id: 'code', label: t('widgetDemo.tabCode') },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="absolute top-4 right-4 z-10">
        <LanguageSwitcher />
      </div>
      {agentId && (
        <Widget
          key={widgetKey}
          agentId={agentId}
          apiUrl="/api"
          wsUrl="/ws"
          variant="floating"
          themeOverride={{
            position: previewPosition,
            primaryColor: previewColor,
            launcherIcon: previewLauncherIcon,
            launcherText: previewLauncherText,
          }}
        />
      )}

      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <div>
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400 transition-colors"
          >
            {t('common.home')}
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {t('widgetDemo.pageTitle')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2">
            {t('widgetDemo.pageSubtitle')}
          </p>
        </div>

        <Card>
          <CardContent className="py-5 space-y-4">
            <div className="space-y-4">
              {customerConfigs.length > 0 ? (
                <Select
                  label={t('widgetDemo.selectFromList')}
                  options={[
                    { value: '', label: t('widgetDemo.manualInput') },
                    ...customerConfigs.map((c) => ({
                      value: c.id,
                      label: `${c.name}${c.enabled ? '' : t('widgetDemo.disabledSuffix')}`,
                    })),
                  ]}
                  value={agentId}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                    applyAgentId(e.target.value)
                  }
                />
              ) : (
                <p className="text-sm text-gray-500">{t('widgetDemo.loginToSelect')}</p>
              )}
              <div className="flex gap-3 items-end min-w-0">
                <Input
                  label={t('widgetDemo.agentIdLabel')}
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  placeholder={t('widgetDemo.agentIdPlaceholder')}
                  className="min-w-0 flex-1"
                />
                <Button
                  size="action"
                  onClick={() => applyAgentId(agentId)}
                  leftIcon={<Play className="w-4 h-4" />}
                >
                  {t('widgetDemo.apply')}
                </Button>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <Select
                  label={t('customerAgents.widgetPosition')}
                  options={[
                    { value: 'right', label: t('customerAgents.positionBottomRight') },
                    { value: 'left', label: t('customerAgents.positionBottomLeft') },
                  ]}
                  value={previewPosition}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                    setPreviewPosition(e.target.value as 'right' | 'left')
                  }
                />
                <Select
                  label={t('customerAgents.launcherIconLabel')}
                  options={[
                    { value: 'chat', label: t('customerAgents.launcherIconChat') },
                    { value: 'bot', label: t('customerAgents.launcherIconBot') },
                    { value: 'spark', label: t('customerAgents.launcherIconSpark') },
                    { value: 'support', label: t('customerAgents.launcherIconSupport') },
                  ]}
                  value={previewLauncherIcon}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                    setPreviewLauncherIcon(e.target.value)
                  }
                />
                <Input
                  label={t('customerAgents.launcherTextLabel')}
                  value={previewLauncherText}
                  onChange={(e) => setPreviewLauncherText(e.target.value)}
                  placeholder={t('customerAgents.launcherTextPlaceholder')}
                />
                <Input
                  label={t('customerAgents.themeColor')}
                  type="text"
                  value={previewColor}
                  onChange={(e) => setPreviewColor(e.target.value || '#3b82f6')}
                  placeholder="#3b82f6"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<RefreshCw className="w-4 h-4" />}
                onClick={() => setWidgetKey((k) => k + 1)}
                disabled={!agentId}
              >
                {t('widgetDemo.refreshPreview')}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<ExternalLink className="w-4 h-4" />}
                onClick={openStandalone}
                disabled={!agentId}
              >
                {t('widgetDemo.openStandalone')}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<ExternalLink className="w-4 h-4" />}
                onClick={openIframePage}
                disabled={!agentId}
              >
                {t('widgetDemo.openIframe')}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
          </CardHeader>
          <CardContent>
            <TabPanel id="preview" activeTab={activeTab}>
              <div className="text-center py-8">
                <MessageCircle className="w-16 h-16 mx-auto mb-4 text-primary-500 opacity-50" />
                {agentId ? (
                  <p className="text-gray-500 dark:text-gray-400">
                    {t('widgetDemo.previewHint')}
                  </p>
                ) : (
                  <p className="text-amber-600 text-sm">{t('widgetDemo.needAgentId')}</p>
                )}
              </div>
            </TabPanel>

            <TabPanel id="code" activeTab={activeTab}>
              <div className="space-y-4">
                <p className="text-sm text-gray-500">
                  {t('widgetDemo.embedHint')}{' '}
                  <code className="text-xs bg-gray-100 px-1 rounded dark:bg-gray-800">&lt;body&gt;</code>
                </p>
                {agentId ? (
                  <>
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="secondary" leftIcon={<Copy className="w-4 h-4" />} onClick={copyEmbed}>
                        {t('widgetDemo.copyCode')}
                      </Button>
                      <Button size="sm" leftIcon={<Play className="w-4 h-4" />} onClick={openStandalone}>
                        {t('widgetDemo.testPreview')}
                      </Button>
                    </div>
                    <pre className="bg-gray-900 text-gray-100 rounded-xl p-4 text-xs overflow-x-auto whitespace-pre-wrap">
                      {embedScript}
                    </pre>
                  </>
                ) : (
                  <p className="text-sm text-amber-600">{t('widgetDemo.needAgentForCode')}</p>
                )}
              </div>
            </TabPanel>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
