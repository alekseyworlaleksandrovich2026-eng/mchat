import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Save } from 'lucide-react'
import api from '@/lib/api'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { Switch } from '@/components/ui/Switch'
import { Tabs, TabPanel } from '@/components/ui/Tabs'
import { Select } from '@/components/ui/Select'
import { toast } from '@/components/ui/Toast'

interface AppSettings {
  site_name: string
  site_description: string
  language: string
  timezone: string
  max_file_size: number
  allowed_file_types: string[]
  enable_websocket: boolean
  enable_streaming: boolean
  rate_limit_per_min: number
  maintenance_mode: boolean
}

export function SettingsPage() {
  const { t } = useTranslation()
  const [settings, setSettings] = useState<AppSettings>({
    site_name: 'MChat',
    site_description: '',
    language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    max_file_size: 10,
    allowed_file_types: ['txt', 'pdf', 'doc', 'docx', 'md'],
    enable_websocket: true,
    enable_streaming: true,
    rate_limit_per_min: 60,
    maintenance_mode: false,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState('general')

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const data = await api.get<AppSettings>('/settings')
      if (data) setSettings(data)
    } catch (err) {
      console.error('Failed to load settings:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.put('/settings', settings)
      toast(t('settings.toastSaved'), { type: 'success' })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t('settings.toastSaveFailed')
      toast(message, { type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const tabs = [
    { id: 'general', label: t('settings.tabGeneral') },
    { id: 'upload', label: t('settings.tabUpload') },
    { id: 'api', label: t('settings.tabApi') },
    { id: 'security', label: t('settings.tabSecurity') },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-10 h-10 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {t('settings.pageTitle')}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t('settings.pageSubtitle')}
          </p>
        </div>
        <Button
          leftIcon={<Save className="w-4 h-4" />}
          onClick={handleSave}
          isLoading={saving}
        >
          {t('common.save')}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        </CardHeader>
        <CardContent>
          <TabPanel id="general" activeTab={activeTab}>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label={t('settings.siteName')}
                  value={settings.site_name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setSettings({ ...settings, site_name: e.target.value })
                  }
                />
                <Select
                  label={t('settings.siteLanguage')}
                  options={[
                    { value: 'zh-CN', label: t('settings.langZh') },
                    { value: 'en-US', label: t('settings.langEn') },
                  ]}
                  value={settings.language}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                    setSettings({ ...settings, language: e.target.value })
                  }
                />
              </div>
              <Textarea
                label={t('settings.siteDescription')}
                value={settings.site_description}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                  setSettings({ ...settings, site_description: e.target.value })
                }
                rows={3}
              />
              <Select
                label={t('settings.timezone')}
                options={[
                  { value: 'Asia/Shanghai', label: 'Asia/Shanghai (UTC+8)' },
                  { value: 'Asia/Tokyo', label: 'Asia/Tokyo (UTC+9)' },
                  { value: 'America/New_York', label: 'America/New_York (UTC-5)' },
                  { value: 'Europe/London', label: 'Europe/London (UTC+0)' },
                ]}
                value={settings.timezone}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                  setSettings({ ...settings, timezone: e.target.value })
                }
              />
            </div>
          </TabPanel>

          <TabPanel id="upload" activeTab={activeTab}>
            <div className="space-y-4">
              <Input
                label={t('settings.maxFileSize')}
                type="number"
                min={1}
                max={100}
                value={settings.max_file_size}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setSettings({
                    ...settings,
                    max_file_size: parseInt(e.target.value, 10),
                  })
                }
              />
              <Input
                label={t('settings.allowedFileTypes')}
                value={settings.allowed_file_types.join(', ')}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setSettings({
                    ...settings,
                    allowed_file_types: e.target.value
                      .split(',')
                      .map((s: string) => s.trim()),
                  })
                }
                placeholder={t('settings.allowedFileTypesPlaceholder')}
              />
            </div>
          </TabPanel>

          <TabPanel id="api" activeTab={activeTab}>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {t('settings.enableWebsocket')}
                  </p>
                  <p className="text-xs text-gray-500">
                    {t('settings.enableWebsocketHint')}
                  </p>
                </div>
                <Switch
                  checked={settings.enable_websocket}
                  onChange={(checked) =>
                    setSettings({ ...settings, enable_websocket: checked })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {t('settings.enableStreaming')}
                  </p>
                  <p className="text-xs text-gray-500">
                    {t('settings.enableStreamingHint')}
                  </p>
                </div>
                <Switch
                  checked={settings.enable_streaming}
                  onChange={(checked) =>
                    setSettings({ ...settings, enable_streaming: checked })
                  }
                />
              </div>
              <Input
                label={t('settings.rateLimit')}
                type="number"
                min={1}
                max={1000}
                value={settings.rate_limit_per_min}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setSettings({
                    ...settings,
                    rate_limit_per_min: parseInt(e.target.value, 10),
                  })
                }
              />
            </div>
          </TabPanel>

          <TabPanel id="security" activeTab={activeTab}>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {t('settings.maintenanceMode')}
                  </p>
                  <p className="text-xs text-gray-500">
                    {t('settings.maintenanceModeHint')}
                  </p>
                </div>
                <Switch
                  checked={settings.maintenance_mode}
                  onChange={(checked) =>
                    setSettings({ ...settings, maintenance_mode: checked })
                  }
                />
              </div>
            </div>
          </TabPanel>
        </CardContent>
      </Card>
    </div>
  )
}
