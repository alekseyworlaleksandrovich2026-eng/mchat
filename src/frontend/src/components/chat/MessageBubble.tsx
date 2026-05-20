import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn, parseDate } from '@/lib/utils'
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
  type OutboundAsset = {
    url?: string
    name?: string
    mime?: string
    type?: string
    title?: string
    source?: string
  }
  const attachments = (message.extra_data?.attachments as Attachment[] | undefined) ?? []
  const isVideo = (item: { url?: string; mime?: string; name?: string; type?: string }) => {
    const mime = String(item.mime || '').toLowerCase()
    if (mime.startsWith('video/')) return true
    const url = String(item.url || item.name || '').toLowerCase()
    return ['.mp4', '.mov', '.m4v', '.webm'].some((ext) => url.endsWith(ext))
  }
  const withResolvedUrl = (att: Attachment) => ({
    ...att,
    url: resolveUploadUrl(att.url),
  })
  const outboundAssets = ((message.extra_data?.outbound_assets as OutboundAsset[] | undefined) ?? [])
    .map((asset) => ({
      ...asset,
      url: resolveUploadUrl(asset.url),
    }))
  const knowledgeHits = ((message.extra_data?.knowledge_hits as Array<Record<string, any>> | undefined) ?? [])
  const autoReplyRuleHits = ((message.extra_data?.auto_reply_rule_hits as Array<Record<string, any>> | undefined) ?? [])
  const knowledgeHitLabels = useMemo(() => {
    const seen = new Set<string>()
    const labels: string[] = []

    for (const hit of knowledgeHits) {
      const rawTitle = String(hit.title || '').trim()
      const label = rawTitle && !/^chunk\s+\d+$/i.test(rawTitle)
        ? rawTitle
        : t('chat.knowledgeHitFallback')
      if (seen.has(label)) {
        continue
      }
      seen.add(label)
      labels.push(label)
    }

    return labels
  }, [knowledgeHits, t])
  const imageAttachments = attachments
    .filter((a) => a.url && String(a.mime || '').startsWith('image/'))
    .map(withResolvedUrl)
  const videoAttachments = attachments
    .filter((a) => a.url && isVideo(a))
    .map(withResolvedUrl)
  const fileAttachments = attachments
    .filter((a) => a.url && !String(a.mime || '').startsWith('image/') && !isVideo(a))
    .map(withResolvedUrl)
  const attachmentUrls = new Set(
    [...imageAttachments, ...videoAttachments, ...fileAttachments].map((att) => att.url).filter(Boolean),
  )
  const explicitAssets = outboundAssets.filter(
    (asset) =>
      !!asset.url &&
      !attachmentUrls.has(asset.url) &&
      asset.source !== 'markdown_link' &&
      asset.source !== 'raw_url',
  )
  const imageAssets = explicitAssets.filter(
    (asset) => asset.type === 'image' || String(asset.mime || '').startsWith('image/'),
  )
  const videoAssets = explicitAssets.filter((asset) => isVideo(asset))
  const fileAndLinkAssets = explicitAssets.filter(
    (asset) => asset.type !== 'image' && !String(asset.mime || '').startsWith('image/') && !isVideo(asset),
  )
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
            {videoAttachments.map((att, i) => (
              <video
                key={`${att.url}-${i}`}
                src={att.url}
                controls
                className="max-w-full max-h-72 rounded-lg"
              />
            ))}
            {fileAndLinkAssets.map((asset, i) => (
              <a
                key={`${asset.url}-${i}`}
                href={asset.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm underline break-all opacity-90"
              >
                {asset.title || asset.name || asset.url}
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
            {(imageAttachments.length > 0 || imageAssets.length > 0 || videoAttachments.length > 0 || videoAssets.length > 0 || fileAttachments.length > 0 || fileAndLinkAssets.length > 0) && (
              <div className="mt-3 space-y-2">
                {imageAttachments.map((asset, i) => (
                  <a
                    key={`${asset.url}-${i}`}
                    href={asset.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <img
                      src={asset.url}
                      alt={asset.name || 'image'}
                      className="max-w-full max-h-64 rounded-lg object-contain border border-gray-200 dark:border-gray-700"
                    />
                  </a>
                ))}
                {imageAssets.map((asset, i) => (
                  <a
                    key={`${asset.url}-explicit-${i}`}
                    href={asset.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <img
                      src={asset.url}
                      alt={asset.name || asset.title || 'image'}
                      className="max-w-full max-h-64 rounded-lg object-contain border border-gray-200 dark:border-gray-700"
                    />
                  </a>
                ))}
                {videoAttachments.map((asset, i) => (
                  <video
                    key={`${asset.url}-${i}`}
                    src={asset.url}
                    controls
                    className="max-w-full max-h-72 rounded-lg border border-gray-200 dark:border-gray-700"
                  />
                ))}
                {videoAssets.map((asset, i) => (
                  <video
                    key={`${asset.url}-explicit-${i}`}
                    src={asset.url}
                    controls
                    className="max-w-full max-h-72 rounded-lg border border-gray-200 dark:border-gray-700"
                  />
                ))}
                {fileAttachments.map((asset, i) => (
                  <a
                    key={`${asset.url}-${i}`}
                    href={asset.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    {asset.name || asset.url}
                  </a>
                ))}
                {fileAndLinkAssets.map((asset, i) => (
                  <a
                    key={`${asset.url}-explicit-${i}`}
                    href={asset.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    {asset.title || asset.name || asset.url}
                  </a>
                ))}
              </div>
            )}
            {(knowledgeHits.length > 0 || autoReplyRuleHits.length > 0) && (
              <div className="mt-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/80 dark:bg-gray-900/20 px-3 py-2 space-y-2 text-xs text-gray-600 dark:text-gray-300">
                {knowledgeHitLabels.length > 0 && (
                  <div>
                    <p className="font-medium text-gray-700 dark:text-gray-200">{t('chat.knowledgeHits')}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {knowledgeHitLabels.map((label, index) => (
                        <span
                          key={`${label}-${index}`}
                          className="rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-2 py-0.5"
                        >
                          {label}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {autoReplyRuleHits.length > 0 && (
                  <div>
                    <p className="font-medium text-gray-700 dark:text-gray-200">{t('chat.autoReplyHits')}</p>
                    <div className="flex flex-col gap-1 mt-1">
                      {autoReplyRuleHits.map((hit, index) => (
                        <span key={`${hit.rule_id || hit.rule_name}-${index}`}>
                          {hit.rule_name || t('chat.autoReplyHitFallback')}
                          {hit.asset_name ? ` · ${hit.asset_name}` : ''}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
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
          {parseDate(message.created_at).toLocaleTimeString(timeLocale, {
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
