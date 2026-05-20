import type { Message } from '@/stores/chat'

/** Turn API attachment paths into browser-loadable URLs (same origin or dev proxy). */
export function resolveUploadUrl(url?: string): string | undefined {
  if (!url) return undefined
  if (url.startsWith('blob:') || url.startsWith('data:')) return url
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/')) return url
  return `/uploads/${url}`
}

type AttachmentMeta = { url?: string; name?: string; mime?: string; pending?: boolean }
type OutboundAssetMeta = {
  url?: string
  name?: string
  mime?: string
  type?: string
  title?: string
  source?: string
}

export function normalizeMessageMedia(message: Message): Message {
  const attachments = message.extra_data?.attachments as AttachmentMeta[] | undefined
  const outboundAssets = message.extra_data?.outbound_assets as OutboundAssetMeta[] | undefined
  if (!attachments?.length && !outboundAssets?.length) return message

  return {
    ...message,
    extra_data: {
      ...message.extra_data,
      attachments: attachments?.map((att) => ({
        ...att,
        url: resolveUploadUrl(att.url),
      })),
      outbound_assets: outboundAssets?.map((asset) => ({
        ...asset,
        url: resolveUploadUrl(asset.url),
      })),
    },
  }
}
