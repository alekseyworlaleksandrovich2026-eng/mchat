import React, { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ExternalLink, Loader2, MessageSquare, X } from 'lucide-react'
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher'

interface ShowcaseSkill {
  id: string
  name: string
  description?: string | null
}

interface ShowcaseTheme {
  primaryColor?: string
  botName?: string
  widgetTitle?: string
}

interface ShowcaseConfig {
  customer_id: string
  name: string
  welcome_message: string
  theme: ShowcaseTheme
  skills: ShowcaseSkill[]
}

interface ShowcaseHubItem {
  customer_id: string
  name: string
  welcome_message: string
  theme: ShowcaseTheme & {
    launcherIcon?: string
    launcherText?: string
  }
  skill_count: number
  skills: ShowcaseSkill[]
}

export function SkillShowcasePage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const agentId = searchParams.get('agentId') || ''
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [config, setConfig] = useState<ShowcaseConfig | null>(null)
  const [activeSkill, setActiveSkill] = useState<ShowcaseSkill | null>(null)
  const [hubItems, setHubItems] = useState<ShowcaseHubItem[]>([])
  // Direct overlay from hub card click (skips detail page)
  const [hubDirectConfig, setHubDirectConfig] = useState<ShowcaseConfig | null>(null)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const endpoint = agentId
          ? `/api/widget/config/${agentId}/showcase`
          : '/api/widget/showcases'
        const resp = await fetch(endpoint)
        if (!resp.ok) {
          const body = await resp.json().catch(() => ({}))
          throw new Error(body.detail || `Load failed (${resp.status})`)
        }
        const data = await resp.json()
        if (!cancelled) {
          if (agentId) {
            setConfig(data as ShowcaseConfig)
            setHubItems([])
            setActiveSkill(null)
          } else {
            setHubItems(((data as { items?: ShowcaseHubItem[] }).items || []))
            setConfig(null)
          }
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : t('showcase.loadFailed'))
          setConfig(null)
          setHubItems([])
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [agentId, t])

  // Listen for close events from embedded iframe chat windows
  useEffect(() => {
    const handler = (e: MessageEvent) => {
      if (e.data?.type === 'mchat:close') {
        setActiveSkill(null)
        setHubDirectConfig(null)
      }
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [])

  const apiBase = useMemo(() => {
    if (typeof window === 'undefined') return '/api'
    return `${window.location.origin}/api`
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="absolute top-4 right-4 z-20">
        <LanguageSwitcher />
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div>
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400 transition-colors"
          >
            {t('common.home')}
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {agentId
              ? config?.theme?.widgetTitle || config?.name || t('showcase.pageTitle')
              : t('showcase.hubTitle')}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {agentId ? t('showcase.pageSubtitle') : t('showcase.hubSubtitle')}
          </p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-16 text-gray-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            {t('showcase.loading')}
          </div>
        )}

        {!loading && error && (
          <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {!loading && !error && !agentId && hubItems.length === 0 && (
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-10 text-center text-gray-500 dark:text-gray-400">
            <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-40" />
            {t('showcase.hubEmpty')}
          </div>
        )}

        {!loading && !error && !agentId && hubItems.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {hubItems.map((item) => (
              <button
                key={item.customer_id}
                type="button"
                onClick={() => {
                  const cfg: ShowcaseConfig = {
                    customer_id: item.customer_id,
                    name: item.name,
                    welcome_message: item.welcome_message,
                    theme: item.theme,
                    skills: item.skills,
                  }
                  setHubDirectConfig(cfg)
                  setActiveSkill(item.skills[0] || null)
                }}
                className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all text-left"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">{item.theme.widgetTitle || item.name}</h2>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                      {item.welcome_message || t('showcase.cardHint')}
                    </p>
                  </div>
                  <div className="w-11 h-11 rounded-2xl bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 flex items-center justify-center shrink-0">
                    <MessageSquare className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2 text-xs text-gray-500 dark:text-gray-400">
                  {item.skills.slice(0, 3).map((skill) => (
                    <span key={skill.id} className="rounded-full bg-gray-100 dark:bg-gray-700 px-2.5 py-1">
                      {skill.name}
                    </span>
                  ))}
                </div>
                <div className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400">
                  {t('showcase.openAgentShowcase', { count: item.skill_count })}
                  <ExternalLink className="w-4 h-4" />
                </div>
              </button>
            ))}
          </div>
        )}

        {!loading && !error && config && config.skills.length === 0 && (
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-10 text-center text-gray-500 dark:text-gray-400">
            <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-40" />
            {t('showcase.emptySkills')}
          </div>
        )}

        {!loading && !error && config && config.skills.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {config.skills.map((skill) => (
              <button
                key={skill.id}
                type="button"
                onClick={() => setActiveSkill(skill)}
                className="text-left rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">{skill.name}</h2>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {skill.description || t('showcase.cardHint')}
                    </p>
                  </div>
                  <div className="w-11 h-11 rounded-2xl bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 flex items-center justify-center shrink-0">
                    <MessageSquare className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400">
                  {t('showcase.openChat')}
                  <ExternalLink className="w-4 h-4" />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {(config || hubDirectConfig) && activeSkill && (() => {
        const effectiveConfig = config || hubDirectConfig!
        const effectiveAgentId = effectiveConfig.customer_id
        const query = new URLSearchParams({
          mode: 'embed',
          agentId: effectiveAgentId,
          apiUrl: apiBase,
          skillId: activeSkill.id,
          botName: `${effectiveConfig.theme?.botName || effectiveConfig.name} · ${activeSkill.name}`,
          primaryColor: effectiveConfig.theme?.primaryColor || '#3b82f6',
          welcomeMessage: effectiveConfig.welcome_message || t('showcase.defaultWelcome'),
        })
        return (
          <div className="fixed inset-0 z-40 bg-black/45 backdrop-blur-sm p-4 md:p-8">
            <div className="mx-auto h-full max-w-6xl grid lg:grid-cols-[320px,1fr] gap-4">
              <div className="rounded-3xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-6 shadow-2xl">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-gray-400">{t('showcase.pageTitle')}</p>
                    <h2 className="mt-2 text-2xl font-bold text-gray-900 dark:text-gray-100">{activeSkill.name}</h2>
                  </div>
                  <button
                    type="button"
                    onClick={() => { setActiveSkill(null); setHubDirectConfig(null) }}
                    className="rounded-xl border border-gray-200 dark:border-gray-700 p-2 text-gray-500 hover:text-gray-900 dark:hover:text-white"
                    title={t('chat.widgetClose')}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
                  {activeSkill.description || t('showcase.cardHint')}
                </p>
                {hubDirectConfig && (
                  <div className="mt-4 border-t border-gray-100 dark:border-gray-700 pt-4">
                    <p className="text-xs text-gray-400 mb-2">{t('showcase.pageSubtitle')}</p>
                    <div className="space-y-1">
                      {hubDirectConfig.skills.map((s) => (
                        <button
                          key={s.id}
                          type="button"
                          onClick={() => setActiveSkill(s)}
                          className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                            activeSkill.id === s.id
                              ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 font-medium'
                              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                          }`}
                        >
                          {s.name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => window.open(`/widget.html?${query.toString()}`, '_blank', 'noopener,noreferrer')}
                  className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400"
                >
                  {t('showcase.openDirect')}
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
              <div className="rounded-3xl overflow-hidden border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-2xl min-h-[70vh]">
                <iframe
                  title={`skill-${activeSkill.id}`}
                  src={`/widget.html?${query.toString()}`}
                  className="w-full h-full min-h-[70vh] border-0"
                  loading="lazy"
                />
              </div>
            </div>
          </div>
        )
      })()}
    </div>
  )
}
