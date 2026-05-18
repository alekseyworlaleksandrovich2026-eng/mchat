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

export function normalizeMessageMedia(message: Message): Message {
  const attachments = message.extra_data?.attachments as AttachmentMeta[] | undefined
  if (!attachments?.length) return message

  return {
    ...message,
    extra_data: {
      ...message.extra_data,
      attachments: attachments.map((att) => ({
        ...att,
        url: resolveUploadUrl(att.url),
      })),
    },
  }
}
