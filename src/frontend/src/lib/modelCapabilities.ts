export interface ModelCapabilities {
  supports_attachments: boolean
  supports_vision: boolean
}

export const DEFAULT_MODEL_CAPABILITIES: ModelCapabilities = {
  supports_attachments: true,
  supports_vision: false,
}

const DOC_ACCEPT =
  '.pdf,.doc,.docx,.txt,.md,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain'

export function attachmentAcceptForCapabilities(
  caps: ModelCapabilities | null | undefined,
): string | undefined {
  if (!caps?.supports_attachments) return undefined
  if (caps.supports_vision) {
    return `image/*,video/mp4,video/quicktime,video/webm,.mp4,.mov,.m4v,.webm,${DOC_ACCEPT}`
  }
  return DOC_ACCEPT
}
