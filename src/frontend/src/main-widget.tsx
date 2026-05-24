import React from 'react'
import ReactDOM from 'react-dom/client'
import '@/i18n'
import { Widget } from './components/widget/Widget'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import './styles/index.css'

const params = new URLSearchParams(window.location.search)
const mode = params.get('mode') || 'page'
const isEmbed = mode === 'embed'

const config = {
  agentId: params.get('agentId') || (window as Window & { __MChatConfig?: { agentId?: string } }).__MChatConfig?.agentId || '',
  apiUrl:
    params.get('apiUrl') ||
    (window as Window & { __MChatConfig?: { apiUrl?: string } }).__MChatConfig?.apiUrl ||
    '/api',
  wsUrl:
    params.get('wsUrl') ||
    (window as Window & { __MChatConfig?: { wsUrl?: string } }).__MChatConfig?.wsUrl ||
    '/ws',
  position: (params.get('position') as 'right' | 'left') || 'right',
  primaryColor: params.get('primaryColor') || '#3b82f6',
  welcomeMessage:
    params.get('welcomeMessage') ||
    '你好！我是智能客服助手，有什么可以帮助你的？',
  botName: params.get('botName') || '智能助手',
  skillId: params.get('skillId') || '',
  launcherIcon: params.get('launcherIcon') || 'chat',
  launcherText: params.get('launcherText') || '',
}

const rootEl = document.getElementById('mchat-widget-root')
if (!rootEl) {
  throw new Error('mchat-widget-root not found')
}

ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <ErrorBoundary>
      <Widget
        variant={isEmbed ? 'iframe' : 'page'}
        defaultOpen={isEmbed}
        agentId={config.agentId}
        apiUrl={config.apiUrl}
        wsUrl={config.wsUrl}
        position={config.position}
        primaryColor={config.primaryColor}
        welcomeMessage={config.welcomeMessage}
        botName={config.botName}
        skillId={config.skillId}
        launcherIcon={config.launcherIcon}
        launcherText={config.launcherText}
      />
    </ErrorBoundary>
  </React.StrictMode>,
)
