import { useMemo } from 'react'
import { Widget } from '@/components/widget/Widget'

function getQueryParams(): Record<string, string> {
  const params = new URLSearchParams(window.location.search)
  const result: Record<string, string> = {}
  params.forEach((value, key) => {
    result[key] = value
  })
  return result
}

declare global {
  interface Window {
    wx?: {
      miniProgram: {
        navigateBack: (options: { delta: number }) => void
        navigateTo: (options: { url: string }) => void
        redirectTo: (options: { url: string }) => void
        postMessage: (options: { data: Record<string, unknown> }) => void
      }
    }
    __wxjs_environment?: string
  }
}

export function WxMiniPage() {
  const params = useMemo(() => getQueryParams(), [])

  const agentId = params.agentId || params.agent_id || ''
  const skillId = params.skillId || params.skill_id || ''
  const apiUrl = params.apiUrl || params.api_url || '/api'

  const missing = !agentId

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {missing ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            padding: 24,
            textAlign: 'center',
            color: '#999',
            fontSize: 14,
            fontFamily:
              '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          }}
        >
          <div>
            <div style={{ marginBottom: 8, fontWeight: 600, color: '#333' }}>
              缺少 Agent ID
            </div>
            <div>
              请在小程序链接中提供 ?agentId= 参数
            </div>
          </div>
        </div>
      ) : (
        <Widget
          variant="page"
          agentId={agentId}
          apiUrl={apiUrl}
          wsUrl="/ws"
          defaultOpen
          skillId={skillId || undefined}
        />
      )}
    </div>
  )
}
