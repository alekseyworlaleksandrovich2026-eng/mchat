import React from 'react'
import ReactDOM from 'react-dom/client'
import '@/i18n'
import { WxMiniPage } from './pages/WxMiniPage'
import './styles/index.css'

const rootEl = document.getElementById('mchat-wx-mini-root')
if (!rootEl) {
  throw new Error('mchat-wx-mini-root not found')
}

ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <WxMiniPage />
  </React.StrictMode>,
)
