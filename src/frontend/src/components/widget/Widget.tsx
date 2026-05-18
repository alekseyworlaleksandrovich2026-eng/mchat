import React, { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { X, Minus, MessageCircle, Loader2, Maximize2, Minimize2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWidgetConfig } from '@/hooks/useWidgetConfig'
import { useWidgetChat } from '@/hooks/useWidgetChat'
import { ChatWindow } from '@/components/chat/ChatWindow'
import { WidgetButton } from './WidgetButton'
import { GithubLink } from '@/components/common/GithubLink'

interface WidgetProps {
  agentId: string
  apiUrl: string
  wsUrl: string
  variant?: 'floating' | 'page' | 'iframe'
  defaultOpen?: boolean
  position?: 'right' | 'left'
  primaryColor?: string
  welcomeMessage?: string
  botName?: string
}

export function Widget({
  agentId,
  apiUrl,
  wsUrl: _wsUrl,
  variant = 'floating',
  defaultOpen = false,
  position = 'right',
  primaryColor = '#3b82f6',
  welcomeMessage,
  botName,
}: WidgetProps) {
  const { t } = useTranslation()
  const isPage = variant === 'page'
  const isIframe = variant === 'iframe'
  const defaultWelcome = welcomeMessage ?? t('customerAgents.defaultWelcome')
  const defaultBotName = botName ?? t('customerAgents.defaultBotName')
  const { config: remoteConfig, loading: configLoading, error: configError } =
    useWidgetConfig(agentId, apiUrl)

  const resolved = useMemo(
    () => ({
      position: (remoteConfig?.position as 'right' | 'left') || position,
      primaryColor: remoteConfig?.theme?.primaryColor || primaryColor,
      welcomeMessage: remoteConfig?.welcome_message || defaultWelcome,
      botName: remoteConfig?.theme?.botName || defaultBotName,
    }),
    [remoteConfig, position, primaryColor, defaultWelcome, defaultBotName],
  )

  const chat = useWidgetChat(agentId, apiUrl, resolved.welcomeMessage)

  const [isOpen, setIsOpen] = useState(isPage || isIframe || defaultOpen)

  const [isMinimized, setIsMinimized] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)

  const postPanelResize = (expanded: boolean) => {
    if (!isIframe) return
    try {
      window.parent.postMessage({ type: 'mchat:resize', expanded }, '*')
    } catch {
      /* cross-origin */
    }
  }

  const setExpanded = (expanded: boolean) => {
    setIsExpanded(expanded)
    postPanelResize(expanded)
  }

  const closeEmbed = () => {
    setExpanded(false)
    try {
      window.parent.postMessage({ type: 'mchat:close' }, '*')
    } catch {
      /* cross-origin */
    }
  }

  if (!agentId) {
    return (
      <div
        className={cn(
          'flex items-center justify-center p-6 text-center text-sm text-gray-500',
          isPage ? 'min-h-screen bg-gray-50' : 'fixed bottom-24 right-6 max-w-xs',
        )}
      >
        {t('chat.missingAgentConfig')}
      </div>
    )
  }

  if (configError && isPage) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="max-w-md rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {configError}
        </div>
      </div>
    )
  }

  const chatBody = (
    <ChatWindow
      messages={chat.messages}
      isStreaming={chat.isStreaming}
      streamingContent={chat.streamingContent}
      onSend={chat.sendMessage}
      title={isPage ? resolved.botName : undefined}
      emptyMessage={resolved.welcomeMessage}
      disabled={chat.isLoading || chat.isStreaming || configLoading}
      loading={chat.historyLoading || configLoading}
      accentColor={resolved.primaryColor}
      headerStyle={{ backgroundColor: resolved.primaryColor }}
      embedded={!isPage}
      speechConfigUrl={`${apiUrl}/widget/${agentId}/speech/config`}
      speechTranscribeUrl={`${apiUrl}/widget/${agentId}/speech/transcribe`}
      showGithubLink={false}
    />
  )

  if (isIframe) {
    return (
      <div className="h-full w-full flex flex-col bg-gray-50 dark:bg-gray-900 overflow-hidden">
        <div
          className="shrink-0 flex items-center justify-between px-4 py-3 text-white"
          style={{ backgroundColor: resolved.primaryColor }}
        >
          <div className="flex items-center gap-2 min-w-0">
            <MessageCircle className="w-5 h-5 shrink-0" />
            <span className="font-medium text-sm truncate">{resolved.botName}</span>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <GithubLink onDark />
            {!isExpanded ? (
              <button
                type="button"
                onClick={() => setExpanded(true)}
                className="p-1 rounded hover:bg-white/20"
                title={t('widgetDemo.fullscreen')}
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setExpanded(false)}
                className="p-1 rounded hover:bg-white/20"
                title={t('widgetDemo.shrink')}
              >
                <Minimize2 className="w-4 h-4" />
              </button>
            )}
            <button
              type="button"
              onClick={closeEmbed}
              className="p-1 rounded hover:bg-white/20"
              title={t('chat.widgetClose')}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
        {chat.error && (
          <div className="shrink-0 mx-2 mt-2 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-xs text-red-600">
            {chat.error}
          </div>
        )}
        <div className="flex-1 min-h-0">{chatBody}</div>
      </div>
    )
  }

  if (isPage) {
    return (
      <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
        {chat.error && (
          <div className="shrink-0 mx-4 mt-2 px-4 py-2 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">
            {chat.error}
            <button
              type="button"
              className="ml-2 underline"
              onClick={() => chat.setError(null)}
            >
              {t('chat.widgetClose')}
            </button>
          </div>
        )}
        <div className="flex-1 min-h-0">{chatBody}</div>
      </div>
    )
  }

  return (
    <>
      {isOpen && !isMinimized && (
        <div
          className={cn(
            'fixed z-[9999] flex flex-col overflow-hidden shadow-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 widget-enter',
            isExpanded
              ? 'inset-3 rounded-2xl'
              : cn(
                  'bottom-24 rounded-2xl',
                  resolved.position === 'right' ? 'right-4' : 'left-4',
                  'w-[min(calc(100vw-2rem),440px)] h-[min(80vh,720px)]',
                ),
          )}
        >
          <div
            className="shrink-0 flex items-center justify-between px-4 py-3 text-white"
            style={{ backgroundColor: resolved.primaryColor }}
          >
            <div className="flex items-center gap-2">
              <MessageCircle className="w-5 h-5" />
              <span className="font-medium text-sm">{resolved.botName}</span>
            </div>
            <div className="flex items-center gap-1">
              <GithubLink onDark />
              {!isExpanded ? (
                <button
                  type="button"
                  onClick={() => setExpanded(true)}
                  className="p-1 rounded hover:bg-white/20"
                  title={t('widgetDemo.fullscreen')}
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setExpanded(false)}
                  className="p-1 rounded hover:bg-white/20"
                  title={t('widgetDemo.shrink')}
                >
                  <Minimize2 className="w-4 h-4" />
                </button>
              )}
              <button
                type="button"
                onClick={() => setIsMinimized(true)}
                className="p-1 rounded hover:bg-white/20"
                title={t('widgetDemo.minimize')}
              >
                <Minus className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false)
                  setExpanded(false)
                }}
                className="p-1 rounded hover:bg-white/20"
                title={t('chat.widgetClose')}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="flex-1 min-h-0 flex flex-col overflow-hidden bg-gray-50 dark:bg-gray-900">
            {chatBody}
          </div>
        </div>
      )}

      {isOpen && isMinimized && (
        <div
          className={cn(
            'fixed bottom-24 z-[9999] rounded-2xl shadow-lg px-4 py-3 text-white cursor-pointer flex items-center gap-2',
            resolved.position === 'right' ? 'right-4' : 'left-4',
          )}
          style={{ backgroundColor: resolved.primaryColor }}
          onClick={() => setIsMinimized(false)}
        >
          <MessageCircle className="w-5 h-5" />
          <span className="text-sm font-medium">{resolved.botName}</span>
        </div>
      )}

      {configError && (
        <div
          className={cn(
            'fixed bottom-24 z-[9998] max-w-xs rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-700',
            resolved.position === 'right' ? 'right-4' : 'left-4',
          )}
        >
          {configError}
        </div>
      )}

      {configLoading && isOpen && (
        <div
          className={cn(
            'fixed bottom-24 z-[9998] rounded-lg bg-white border px-3 py-2 text-xs text-gray-600 shadow flex items-center gap-2',
            resolved.position === 'right' ? 'right-4' : 'left-4',
          )}
        >
          <Loader2 className="w-4 h-4 animate-spin" />
          {t('chat.widgetLoadingConfig')}
        </div>
      )}

      {(!isOpen || isMinimized) && (
      <WidgetButton
        isOpen={isOpen}
        onClick={() => {
          setIsOpen(!isOpen)
          setIsMinimized(false)
          setExpanded(false)
        }}
        position={resolved.position}
        primaryColor={resolved.primaryColor}
      />
      )}
    </>
  )
}
