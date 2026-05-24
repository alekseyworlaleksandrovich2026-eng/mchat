import React, { useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { MessageSquare } from 'lucide-react'
import { GithubLink } from '@/components/common/GithubLink'
import { MessageBubble } from './MessageBubble'
import { ChatInput } from './ChatInput'
import { ChatSendOptions, Message } from '@/stores/chat'
import { cn } from '@/lib/utils'

interface ChatWindowProps {
  messages: Message[]
  isStreaming: boolean
  streamingContent: string
  onSend: (content: string, options?: ChatSendOptions) => void
  title?: string
  emptyMessage?: string
  disabled?: boolean
  loading?: boolean
  accentColor?: string
  headerStyle?: React.CSSProperties
  /** Floating widget: tighter padding, wider assistant bubbles */
  embedded?: boolean
  speechTranscribeUrl?: string
  speechConfigUrl?: string
  showGithubLink?: boolean
  allowAssistantMode?: boolean
  allowOutboundLinks?: boolean
  defaultSendRole?: 'user' | 'assistant'
}

export function ChatWindow({
  messages,
  isStreaming,
  streamingContent,
  onSend,
  title,
  emptyMessage,
  disabled = false,
  loading = false,
  accentColor,
  headerStyle,
  embedded = false,
  speechTranscribeUrl,
  speechConfigUrl,
  showGithubLink = true,
  allowAssistantMode = false,
  allowOutboundLinks = false,
  defaultSendRole = 'user',
}: ChatWindowProps) {
  const { t } = useTranslation()
  const resolvedEmpty = emptyMessage ?? t('chat.emptyStart')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, streamingContent])

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      {title && (
        <div
          className="shrink-0 border-b border-gray-200 dark:border-gray-700 px-6 py-4 text-white"
          style={headerStyle}
        >
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 opacity-90 shrink-0" />
            <h2 className="text-lg font-semibold flex-1 truncate">{title}</h2>
            {showGithubLink && (
              <GithubLink onDark className="shrink-0 ml-auto" />
            )}
          </div>
        </div>
      )}

      {/* Messages area */}
      <div
        ref={containerRef}
        className={cn(
          'flex-1 overflow-y-auto w-full space-y-4 scrollbar-thin',
          embedded ? 'px-3 py-4' : 'px-4 py-6',
        )}
      >
        {loading ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            {t('chat.loadingHistory')}
          </div>
        ) : messages.length === 0 && !isStreaming ? (
          <div
            className={cn(
              'flex flex-col text-gray-400 dark:text-gray-500',
              embedded
                ? 'items-start pt-2'
                : 'items-center justify-center h-full',
            )}
          >
            <MessageSquare className={cn('opacity-50', embedded ? 'w-8 h-8 mb-2' : 'w-12 h-12 mb-3')} />
            <p className={cn('text-sm', embedded && 'text-left leading-relaxed')}>{resolvedEmpty}</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                accentColor={accentColor}
                compact={embedded}
              />
            ))}
            {isStreaming && (
              <MessageBubble
                message={{
                  id: 'streaming',
                  conversation_id: '',
                  role: 'assistant',
                  content: streamingContent,
                  content_type: 'text',
                  created_at: new Date().toISOString(),
                }}
                isStreaming
                streamingContent={streamingContent}
                accentColor={accentColor}
                compact={embedded}
              />
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <ChatInput
        onSend={onSend}
        disabled={disabled}
        compact={embedded}
        singleLine={embedded}
        speechTranscribeUrl={speechTranscribeUrl}
        speechConfigUrl={speechConfigUrl}
        allowAssistantMode={allowAssistantMode}
        allowOutboundLinks={allowOutboundLinks}
        defaultSendRole={defaultSendRole}
      />
    </div>
  )
}
