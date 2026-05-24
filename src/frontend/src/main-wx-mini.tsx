import React from 'react'
import ReactDOM from 'react-dom/client'
import '@/i18n'
import { WxMiniPage } from './pages/WxMiniPage'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import './styles/index.css'

const rootEl = document.getElementById('mchat-wx-mini-root')
if (!rootEl) {
  throw new Error('mchat-wx-mini-root not found')
}

ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <ErrorBoundary>
      <WxMiniPage />
    </ErrorBoundary>
  </React.StrictMode>,
)
