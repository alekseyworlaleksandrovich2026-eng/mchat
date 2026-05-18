import React, { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Palette,
  Globe,
  MessageSquare,
  Save,
  Smartphone,
  Plus,
  Code,
  Copy,
  Bot,
  Sparkles,
  BookOpen,
} from 'lucide-react'
import i18n from '@/i18n'
import api from '@/lib/api'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { Tabs, TabPanel } from '@/components/ui/Tabs'
import { Select } from '@/components/ui/Select'
import { toast } from '@/components/ui/Toast'

interface SkillOption {
  id: string
  name: string
  description: string | null
  skill_type: string
  enabled: boolean
}

interface KnowledgeBaseOption {
  id: string
  name: string
}

interface CustomerServiceConfig {
  id: string
  name: string
  user_id?: string
  ai_config_id: string | null
  skill_ids: string[] | null
  knowledge_base_ids: string[] | null
  welcome_message: string | null
  offline_message: string | null
  theme: {
    primaryColor?: string
    buttonColor?: string
    botName?: string
    widgetTitle?: string
    showBranding?: boolean
  } | null
  domains: string | null
  position: string
  enabled: boolean
  widget_session_ttl_hours?: number
  created_at?: string
  updated_at?: string
}

function emptyCustomerConfig(): CustomerServiceConfig {
  return {
    id: '',
    name: i18n.t('customerAgents.defaultConfigName'),
    ai_config_id: null,
    skill_ids: null,
    knowledge_base_ids: null,
    welcome_message: i18n.t('customerAgents.defaultWelcome'),
    offline_message: i18n.t('customerAgents.defaultOffline'),
    theme: {
      primaryColor: '#3b82f6',
      buttonColor: '#3b82f6',
      botName: i18n.t('customerAgents.defaultBotName'),
      widgetTitle: i18n.t('customerAgents.defaultWidgetTitle'),
      showBranding: true,
    },
    domains: null,
    position: 'right',
    enabled: true,
    widget_session_ttl_hours: 24,
  }
}

export function CustomerConfig() {
  const { t } = useTranslation()
  const [configs, setConfigs] = useState<CustomerServiceConfig[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [config, setConfig] = useState<CustomerServiceConfig>(() => emptyCustomerConfig())
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState('capabilities')
  const [domainInput, setDomainInput] = useState('')
  const [aiConfigs, setAiConfigs] = useState<{ id: string; name: string }[]>([])
  const [skills, setSkills] = useState<SkillOption[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseOption[]>([])

  const skillTypeLabel = (skillType: string) =>
    skillType === 'builtin' ? t('skills.builtin') : t('skills.custom')

  const tabs = useMemo(
    () => [
      { id: 'capabilities', label: t('customerAgents.tabCapabilities'), icon: <Bot className="w-4 h-4" /> },
      { id: 'widget', label: t('customerAgents.tabWidget'), icon: <Palette className="w-4 h-4" /> },
      { id: 'domain', label: t('customerAgents.tabDomain'), icon: <Globe className="w-4 h-4" /> },
      { id: 'message', label: t('customerAgents.tabMessage'), icon: <MessageSquare className="w-4 h-4" /> },
      { id: 'embed', label: t('customerAgents.tabEmbed'), icon: <Code className="w-4 h-4" /> },
    ],
    [t],
  )

  useEffect(() => {
    loadConfigs()
    loadAiConfigs()
    loadSkills()
    loadKnowledgeBases()
  }, [])

  const loadAiConfigs = async () => {
    try {
      const data = await api.get<{ id: string; name: string }[]>('/agents/ai-configs')
      setAiConfigs(data.map((c) => ({ id: c.id, name: c.name })))
    } catch {
      /* optional */
    }
  }

  const loadSkills = async () => {
    try {
      const data = await api.get<SkillOption[]>('/skills')
      setSkills(data.filter((s) => s.enabled))
    } catch {
      /* optional */
    }
  }

  const loadKnowledgeBases = async () => {
    try {
      const data = await api.get<KnowledgeBaseOption[]>('/knowledge/bases')
      setKnowledgeBases(data)
    } catch {
      /* optional */
    }
  }

  const useAllSkills = config.skill_ids == null
  const useAllKbs = config.knowledge_base_ids == null
  const selectedSkillIds = useAllSkills ? [] : (config.skill_ids ?? [])
  const selectedKbIds = useAllKbs ? [] : (config.knowledge_base_ids ?? [])

  const toggleSkill = (skillId: string) => {
    const current = useAllSkills ? [] : [...selectedSkillIds]
    const next = current.includes(skillId)
      ? current.filter((id) => id !== skillId)
      : [...current, skillId]
    setConfig({ ...config, skill_ids: next })
  }

  const toggleKnowledgeBase = (kbId: string) => {
    const current = useAllKbs ? [] : [...selectedKbIds]
    const next = current.includes(kbId)
      ? current.filter((id) => id !== kbId)
      : [...current, kbId]
    setConfig({ ...config, knowledge_base_ids: next })
  }

  const loadConfigs = async () => {
    try {
      const data = await api.get<CustomerServiceConfig[]>('/agents/customer-configs')
      setConfigs(data)
      if (data.length > 0) {
        setSelectedId(data[0].id)
        setConfig(data[0])
      }
    } catch (err) {
      console.error('Failed to load configs:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = (id: string) => {
    setSelectedId(id)
    const found = configs.find((c) => c.id === id)
    if (found) setConfig(found)
  }

  const handleCreate = async () => {
    try {
      const created = await api.post<CustomerServiceConfig>('/agents/customer-configs', {
        name: t('customerAgents.newConfigName'),
        position: 'right',
        enabled: true,
      })
      setConfigs((prev) => [...prev, created])
      setSelectedId(created.id)
      setConfig(created)
      toast(t('customerAgents.toastCreated'), { type: 'success' })
    } catch (err: any) {
      toast(t('customerAgents.toastCreateFailed'), { type: 'error', message: err.message })
    }
  }

  const handleSave = async () => {
    if (!selectedId) {
      try {
        const created = await api.post<CustomerServiceConfig>('/agents/customer-configs', {
          name: config.name,
          ai_config_id: config.ai_config_id,
          skill_ids: config.skill_ids,
          knowledge_base_ids: config.knowledge_base_ids,
          welcome_message: config.welcome_message,
          offline_message: config.offline_message,
          theme: config.theme,
          domains: config.domains,
          position: config.position,
          enabled: config.enabled,
          widget_session_ttl_hours: config.widget_session_ttl_hours ?? 24,
        })
        setConfigs((prev) => [...prev, created])
        setSelectedId(created.id)
        setConfig(created)
        toast(t('customerAgents.toastSaveSuccess'), { type: 'success' })
      } catch (err: any) {
        toast(t('customerAgents.toastSaveFailed'), { type: 'error', message: err.message })
      }
      return
    }

    setSaving(true)
    try {
      await api.put(`/agents/customer-configs/${selectedId}`, {
        name: config.name,
        ai_config_id: config.ai_config_id,
        skill_ids: config.skill_ids,
        knowledge_base_ids: config.knowledge_base_ids,
        welcome_message: config.welcome_message,
        offline_message: config.offline_message,
        theme: config.theme,
        domains: config.domains,
        position: config.position,
        enabled: config.enabled,
        widget_session_ttl_hours: config.widget_session_ttl_hours ?? 24,
      })
      toast(t('customerAgents.toastSaveSuccess'), { type: 'success' })
    } catch (err: any) {
      toast(t('customerAgents.toastSaveFailed'), { type: 'error', message: err.message })
    } finally {
      setSaving(false)
    }
  }

  const updateTheme = (key: string, value: any) => {
    setConfig({
      ...config,
      theme: { ...(config.theme || {}), [key]: value },
    })
  }

  const addDomain = () => {
    const domain = domainInput.trim().toLowerCase()
    if (!domain) return
    const current = config.domains ? config.domains.split(',').map((d) => d.trim()).filter(Boolean) : []
    if (!current.includes(domain)) {
      current.push(domain)
      setConfig({ ...config, domains: current.join(',') })
    }
    setDomainInput('')
  }

  const removeDomain = (domain: string) => {
    const current = config.domains ? config.domains.split(',').map((d) => d.trim()).filter(Boolean) : []
    setConfig({ ...config, domains: current.filter((d) => d !== domain).join(',') })
  }

  const theme = config.theme || {}
  const domainList = config.domains ? config.domains.split(',').map((d) => d.trim()).filter(Boolean) : []
  const primaryColor = theme.primaryColor || '#3b82f6'

  const apiBase =
    typeof window !== 'undefined'
      ? `${window.location.origin}/api`
      : 'https://your-domain.com/api'
  const widgetOrigin =
    typeof window !== 'undefined' ? window.location.origin : 'https://your-domain.com'

  const defaultBot = i18n.t('customerAgents.defaultBotName')

  const embedScript = selectedId
    ? `<!-- MChat Widget -->
<script
  src="${widgetOrigin}/widget-loader.js"
  data-mchat-url="${apiBase}"
  data-agent-id="${selectedId}"
  data-position="${config.position}"
  data-primary-color="${primaryColor}"
  data-welcome-message="${(config.welcome_message || '').replace(/"/g, '&quot;')}"
  data-bot-name="${theme.botName || defaultBot}"
></script>`
    : ''

  const copyEmbedCode = async () => {
    if (!embedScript) return
    try {
      await navigator.clipboard.writeText(embedScript)
      toast(t('customerAgents.toastCopySuccess'), { type: 'success' })
    } catch {
      toast(t('customerAgents.toastCopyFailed'), { type: 'error' })
    }
  }

  const previewPositionLabel =
    config.position === 'right'
      ? t('customerAgents.positionBottomRight')
      : t('customerAgents.positionBottomLeft')

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Select
            label=""
            options={configs.map((c) => ({ value: c.id, label: c.name }))}
            value={selectedId || ''}
            onChange={(e: any) => handleSelect(e.target.value)}
            className="w-52"
          />
          <Button size="action" variant="ghost" leftIcon={<Plus className="w-4 h-4" />} onClick={handleCreate}>
            {t('customerAgents.new')}
          </Button>
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
          <div className="flex items-center gap-2 mb-2">
            <Input
              label=""
              value={config.name}
              onChange={(e: any) => setConfig({ ...config, name: e.target.value })}
              placeholder={t('customerAgents.configNamePlaceholder')}
              className="w-48"
            />
          </div>
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        </CardHeader>
        <CardContent>
          <TabPanel id="capabilities" activeTab={activeTab}>
            <div className="space-y-6">
              <Input
                label={t('customerAgents.widgetSessionTtl')}
                type="number"
                min={0}
                max={8760}
                value={config.widget_session_ttl_hours ?? 24}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setConfig({
                    ...config,
                    widget_session_ttl_hours: Math.max(
                      0,
                      parseInt(e.target.value, 10) || 0,
                    ),
                  })
                }
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 -mt-4">
                {t('customerAgents.widgetSessionHint')}
              </p>
              <Select
                label={t('customerAgents.bindAiModel')}
                options={[
                  { value: '', label: t('customerAgents.useDefaultModel') },
                  ...aiConfigs.map((c) => ({ value: c.id, label: c.name })),
                ]}
                value={config.ai_config_id || ''}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                  setConfig({
                    ...config,
                    ai_config_id: e.target.value || null,
                  })
                }
              />
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-primary-600" />
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">{t('customerAgents.skillsSection')}</h4>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  {t('customerAgents.skillsHint')}
                </p>
                {skills.map((skill) => (
                  <label key={skill.id} className="flex gap-2 text-sm text-gray-700 dark:text-gray-300 block mb-1">
                    <input
                      type="checkbox"
                      checked={useAllSkills || selectedSkillIds.includes(skill.id)}
                      onChange={() => {
                        if (useAllSkills) setConfig({ ...config, skill_ids: [skill.id] })
                        else toggleSkill(skill.id)
                      }}
                    />
                    {skill.name} ({skillTypeLabel(skill.skill_type)})
                  </label>
                ))}
                {!useAllSkills && (
                  <button type="button" className="text-xs text-primary-600" onClick={() => setConfig({ ...config, skill_ids: null })}>{t('customerAgents.allSkills')}</button>
                )}
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="w-4 h-4" />
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">{t('customerAgents.knowledgeSection')}</h4>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{t('customerAgents.knowledgeHint')}</p>
                {knowledgeBases.map((kb) => (
                  <label key={kb.id} className="flex gap-2 text-sm text-gray-700 dark:text-gray-300 block mb-1">
                    <input
                      type="checkbox"
                      checked={useAllKbs || selectedKbIds.includes(kb.id)}
                      onChange={() => {
                        if (useAllKbs) setConfig({ ...config, knowledge_base_ids: [kb.id] })
                        else toggleKnowledgeBase(kb.id)
                      }}
                    />
                    {kb.name}
                  </label>
                ))}
                {!useAllKbs && (
                  <button type="button" className="text-xs text-primary-600" onClick={() => setConfig({ ...config, knowledge_base_ids: null })}>{t('customerAgents.allKnowledgeBases')}</button>
                )}
              </div>
            </div>
          </TabPanel>

          <TabPanel id="widget" activeTab={activeTab}>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label={t('customerAgents.widgetTitleLabel')}
                  value={theme.widgetTitle || config.name}
                  onChange={(e: any) => updateTheme('widgetTitle', e.target.value)}
                />
                <Input
                  label={t('customerAgents.botNameLabel')}
                  value={theme.botName || defaultBot}
                  onChange={(e: any) => updateTheme('botName', e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('customerAgents.themeColor')}
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="color"
                      value={primaryColor}
                      onChange={(e) => updateTheme('primaryColor', e.target.value)}
                      className="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
                    />
                    <input
                      type="text"
                      value={primaryColor}
                      onChange={(e) => updateTheme('primaryColor', e.target.value)}
                      className="block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-gray-200"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('customerAgents.widgetPosition')}
                  </label>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setConfig({ ...config, position: 'right' })}
                      className={`flex-1 px-4 py-2 rounded-lg border text-sm transition-colors ${
                        config.position === 'right'
                          ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                          : 'border-gray-300 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400'
                      }`}
                    >
                      <Smartphone className="w-4 h-4 mx-auto mb-1" />
                      {t('customerAgents.positionBottomRight')}
                    </button>
                    <button
                      type="button"
                      onClick={() => setConfig({ ...config, position: 'left' })}
                      className={`flex-1 px-4 py-2 rounded-lg border text-sm transition-colors ${
                        config.position === 'left'
                          ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                          : 'border-gray-300 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400'
                      }`}
                    >
                      <Smartphone className="w-4 h-4 mx-auto mb-1" />
                      {t('customerAgents.positionBottomLeft')}
                    </button>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{t('customerAgents.previewLabel')}</p>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: primaryColor }} />
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    {theme.widgetTitle || config.name} - {theme.botName || defaultBot}
                  </span>
                  <span className="text-xs text-gray-400">
                    {t('customerAgents.previewPositionSuffix', { position: previewPositionLabel })}
                  </span>
                </div>
              </div>
            </div>
          </TabPanel>

          <TabPanel id="domain" activeTab={activeTab}>
            <div className="space-y-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('customerAgents.domainHint')}
              </p>
              <div className="flex gap-2">
                <Input
                  placeholder={t('customerAgents.domainPlaceholder')}
                  value={domainInput}
                  onChange={(e) => setDomainInput(e.target.value)}
                  onKeyDown={(e: any) => e.key === 'Enter' && addDomain()}
                />
                <Button variant="secondary" onClick={addDomain}>
                  {t('customerAgents.add')}
                </Button>
              </div>
              {domainList.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {domainList.map((domain) => (
                    <span
                      key={domain}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 text-sm text-gray-700 dark:text-gray-300"
                    >
                      <Globe className="w-3.5 h-3.5" />
                      {domain}
                      <button
                        onClick={() => removeDomain(domain)}
                        className="ml-1 text-gray-400 hover:text-red-500"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </TabPanel>

          <TabPanel id="message" activeTab={activeTab}>
            <div className="space-y-4">
              <Textarea
                label={t('customerAgents.welcomeMessage')}
                value={config.welcome_message || ''}
                onChange={(e: any) =>
                  setConfig({ ...config, welcome_message: e.target.value })
                }
                rows={4}
                placeholder={t('customerAgents.welcomePlaceholder')}
              />
              <Textarea
                label={t('customerAgents.offlineMessage')}
                value={config.offline_message || ''}
                onChange={(e: any) =>
                  setConfig({ ...config, offline_message: e.target.value })
                }
                rows={3}
                placeholder={t('customerAgents.offlinePlaceholder')}
              />
            </div>
          </TabPanel>

          <TabPanel id="embed" activeTab={activeTab}>
            <div className="space-y-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('customerAgents.embedHint')}
              </p>
              {selectedId ? (
                <>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs text-gray-500 font-mono">Agent ID: {selectedId}</span>
                    <Button size="sm" variant="secondary" leftIcon={<Copy className="w-4 h-4" />} onClick={copyEmbedCode}>
                      {t('customerAgents.copyCode')}
                    </Button>
                  </div>
                  <pre className="bg-gray-900 text-gray-100 rounded-xl p-4 text-xs overflow-x-auto whitespace-pre-wrap">
                    {embedScript}
                  </pre>
                  <div className="flex flex-wrap gap-3 text-xs">
                    <a
                      className="text-primary-600 hover:underline"
                      href={`/widget?agentId=${selectedId}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {t('customerAgents.openStandaloneChat')}
                    </a>
                    <a
                      className="text-primary-600 hover:underline"
                      href={`/widget/demo?agentId=${selectedId}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {t('customerAgents.openWidgetDemo')}
                    </a>
                    <a
                      className="text-primary-600 hover:underline"
                      href={`/widget.html?agentId=${selectedId}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {t('customerAgents.openIframePage')}
                    </a>
                  </div>
                </>
              ) : (
                <p className="text-sm text-amber-600">{t('customerAgents.saveFirstForEmbed')}</p>
              )}
            </div>
          </TabPanel>
        </CardContent>
      </Card>
    </div>
  )
}
