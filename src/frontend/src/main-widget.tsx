import React from 'react'
import ReactDOM from 'react-dom/client'
import { Widget } from './components/widget/Widget'
import './styles/index.css'

// Parse configuration from URL parameters or window.__MChatConfig
const params = new URLSearchParams(window.location.search)
const config = {
  agentId: params.get('agentId') || (window as any).__MChatConfig?.agentId || '',
  apiUrl: params.get('apiUrl') || (window as any).__MChatConfig?.apiUrl || '/api',
  wsUrl: params.get('wsUrl') || (window as any).__MChatConfig?.wsUrl || '/ws',
  position: (params.get('position') as 'right' | 'left') || 'right',
  primaryColor: params.get('primaryColor') || '#3b82f6',
  welcomeMessage: params.get('welcomeMessage') || '你好！我是智能客服助手，有什么可以帮助你的？',
  botName: params.get('botName') || '智能助手',
}

ReactDOM.createRoot(document.getElementById('mchat-widget-root')!).render(
  <React.StrictMode>
    <Widget
      variant="page"
      defaultOpen
      agentId={config.agentId}
      apiUrl={config.apiUrl}
      wsUrl={config.wsUrl}
      position={config.position}
      primaryColor={config.primaryColor}
      welcomeMessage={config.welcomeMessage}
      botName={config.botName}
    />
  </React.StrictMode>,
)
