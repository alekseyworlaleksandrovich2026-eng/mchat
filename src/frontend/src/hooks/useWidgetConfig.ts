import { useEffect, useState } from 'react'

export interface WidgetRemoteConfig {
  id: string
  name: string
  welcome_message: string
  offline_message: string | null
  position: 'left' | 'right'
  theme: {
    primaryColor?: string
    botName?: string
    widgetTitle?: string
    launcherIcon?: string
    launcherText?: string
    showcaseSkillIds?: string[]
  }
  enabled: boolean
  subscription_active?: boolean
  pre_chat_fields?: Array<{
    key: string
    label: string
    required?: boolean
    type?: string
  }>
}

export function useWidgetConfig(agentId: string, apiUrl: string) {
  const [config, setConfig] = useState<WidgetRemoteConfig | null>(null)
  const [loading, setLoading] = useState(Boolean(agentId))
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!agentId) {
      setLoading(false)
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    const base = apiUrl.replace(/\/$/, '')
    fetch(`${base}/widget/config/${agentId}/full`)
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body.detail || `加载配置失败 (${res.status})`)
        }
        return res.json()
      })
      .then((data: WidgetRemoteConfig) => {
        if (!cancelled) {
          setConfig(data)
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message)
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [agentId, apiUrl])

  return { config, loading, error }
}
