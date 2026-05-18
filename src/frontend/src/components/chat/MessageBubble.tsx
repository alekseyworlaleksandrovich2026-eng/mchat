import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import { Message } from '@/stores/chat'
import { Avatar } from '@/components/ui/Avatar'
import { createMarkdownComponents } from './markdownComponents'
import { useThrottledValue } from '@/hooks/useThrottledValue'
import { resolveUploadUrl } from '@/lib/mediaUrl'
import { prepareAssistantMarkdown } from '@/lib/patentMessage'

interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
  streamingContent?: string
  /** User bubble background (e.g. widget theme color) */
  accentColor?: string
  /** Narrow container (floating widget) — assistant bubbles use more width */
  compact?: boolean
}

export function MessageBubble({
  message,
  isStreaming = false,
  streamingContent,
  accentColor,
  compact = false,
}: MessageBubbleProps) {
  const { t, i18n } = useTranslation()
  const [copied, setCopied] = React.useState(false)
  const isUser = message.role === 'user'
  const timeLocale = i18n.language?.startsWith('zh') ? 'zh-CN' : 'en-US'

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback
    }
  }

  const markdownComponents = useMemo(
    () => createMarkdownComponents(handleCopy, copied),
    [copied],
  )

  const displayContent = isStreaming ? streamingContent || '' : message.content
  const throttledContent = useThrottledValue(displayContent, isStreaming ? 50 : 0)
  const assistantText = prepareAssistantMarkdown(throttledContent)

  type Attachment = { url?: string; name?: string; mime?: string }
  const attachments = (message.extra_data?.attachments as Attachment[] | undefined) ?? []
  const withResolvedUrl = (att: Attachment) => ({
    ...att,
    url: resolveUploadUrl(att.url),
  })
  const imageAttachments = attachments
    .filter((a) => a.url && String(a.mime || '').startsWith('image/'))
    .map(withResolvedUrl)
  const fileAttachments = attachments
    .filter((a) => a.url && !String(a.mime || '').startsWith('image/'))
    .map(withResolvedUrl)
  const caption =
    attachments.length > 0 &&
    displayContent &&
    attachments.some((a) => a.name === displayContent)
      ? ''
      : displayContent

  return (
    <div
      className={cn(
        'flex gap-2.5 message-enter w-full',
        isUser ? 'flex-row-reverse' : 'flex-row',
      )}
    >
      <Avatar
        size="md"
        name={isUser ? t('chat.userLabel') : t('chat.aiLabel')}
        className={cn(
          'shrink-0',
          isUser ? 'bg-primary-500' : 'bg-gray-500',
        )}
      />

      <div
        className={cn(
          'rounded-2xl px-4 py-3 min-w-0',
          isUser
            ? cn(
                'max-w-[75%] text-white rounded-tr-sm',
                !accentColor && 'bg-primary-600',
              )
            : cn(
                'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-tl-sm',
                compact ? 'flex-1 max-w-none' : 'max-w-[85%]',
              ),
        )}
        style={isUser && accentColor ? { backgroundColor: accentColor } : undefined}
      >
        {isUser ? (
          <div className="space-y-2">
            {imageAttachments.map((att, i) => (
              <a
                key={`${att.url}-${i}`}
                href={att.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block"
              >
                <img
                  src={att.url}
                  alt={att.name || 'image'}
                  className="max-w-full max-h-64 rounded-lg object-contain"
                />
              </a>
            ))}
            {fileAttachments.map((att, i) => (
              <a
                key={`${att.url}-${i}`}
                href={att.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm underline break-all opacity-90"
              >
                {att.name || 'attachment'}
              </a>
            ))}
            {caption ? (
              <p className="text-sm whitespace-pre-wrap break-words">{caption}</p>
            ) : null}
            {!caption && attachments.length === 0 ? (
              <p className="text-sm whitespace-pre-wrap break-words">{displayContent}</p>
            ) : null}
          </div>
        ) : (
          <div className="max-w-none break-words text-gray-800 dark:text-gray-200">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {assistantText}
            </ReactMarkdown>
            {isStreaming && (
              <span className="cursor-blink inline-block w-[2px] h-4 bg-current ml-0.5 align-middle" />
            )}
          </div>
        )}

        <p
          className={cn(
            'text-xs mt-1.5',
            isUser
              ? accentColor
                ? 'text-white/70'
                : 'text-primary-100'
              : 'text-gray-500 dark:text-gray-400',
          )}
        >
          {new Date(message.created_at).toLocaleTimeString(timeLocale, {
            hour: '2-digit',
            minute: '2-digit',
          })}
          {isStreaming && (
            <span className="ml-2 text-primary-500 animate-pulse">
              {t('chat.typing')}
            </span>
          )}
        </p>
      </div>
    </div>
  )
}
