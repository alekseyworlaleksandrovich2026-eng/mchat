import { create } from 'zustand'
import api from '@/lib/api'
import { normalizeMessageMedia } from '@/lib/mediaUrl'

export type MessageRole = 'user' | 'assistant' | 'system'

export interface OutboundAsset {
  type?: 'image' | 'file' | 'link'
  name?: string
  title?: string
  url: string
  mime?: string
  source?: string
}

export interface ChatSendOptions {
  file?: File
  role?: Exclude<MessageRole, 'system'>
  outboundAssets?: OutboundAsset[]
}

function dedupeMessages(messages: Message[]): Message[] {
  const seen = new Set<string>()
  const out: Message[] = []
  for (const m of messages) {
    const key =
      m.role === 'assistant' ? `a:${m.content}` : `u:${m.id}:${m.content}`
    if (seen.has(key)) continue
    seen.add(key)
    out.push(m)
  }
  return out
}

export interface Message {
  id: string
  conversation_id: string
  role: MessageRole
  content: string
  content_type?: 'text' | 'image' | 'file' | 'video'
  extra_data?: Record<string, any>
  created_at: string
}

export interface Conversation {
  id: string
  title: string | null
  status: 'active' | 'closed'
  conversation_type?: string
  user_id?: string | null
  username?: string | null
  first_user_message_preview?: string | null
  visitor_id: string | null
  client_ip?: string | null
  contact_info: string | null
  customer_id?: string | null
  created_at: string
  updated_at: string
  last_seen_at: string
  user_message_count?: number
  ai_message_count?: number
  total_message_count?: number
}

interface ChatState {
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: Message[]
  isStreaming: boolean
  streamingContent: string
  isLoading: boolean
  error: string | null

  fetchConversations: () => Promise<void>
  fetchMessages: (conversationId: string) => Promise<void>
  sendMessage: (conversationId: string, content: string, options?: ChatSendOptions) => Promise<void>
  createConversation: (title?: string) => Promise<Conversation>
  clearCurrentConversation: () => void
  addMessage: (message: Message) => void
  appendToStream: (content: string) => void
  endStream: () => void
  setError: (error: string | null) => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isStreaming: false,
  streamingContent: '',
  isLoading: false,
  error: null,

  fetchConversations: async () => {
    set({ isLoading: true })
    try {
      const data = await api.get<{ items: Conversation[]; total: number }>('/chat/conversations')
      set({ conversations: data.items || [], isLoading: false })
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
    }
  },

  fetchMessages: async (conversationId: string) => {
    set({ isLoading: true, isStreaming: false, streamingContent: '' })
    try {
      const resp = await api.get<{ messages: Message[] }>(`/chat/conversations/${conversationId}`)
      set({
        messages: dedupeMessages((resp.messages || []).map(normalizeMessageMedia)),
        isLoading: false,
      })
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
    }
  },

  sendMessage: async (conversationId: string, content: string, options?: ChatSendOptions) => {
    const file = options?.file
    const role = options?.role || 'user'
    const outboundAssets = options?.outboundAssets || []
    const shouldStream = role === 'user'
    const tempId = `temp-${Date.now()}`
    const previewUrl =
      file && file.type.startsWith('image/')
        ? URL.createObjectURL(file)
        : undefined

    const extraData: Record<string, any> = {}
    if (file) {
      extraData.attachments = [
        {
          name: file.name,
          mime: file.type,
          url: previewUrl,
          pending: true,
        },
      ]
    }
    if (outboundAssets.length > 0) {
      extraData.outbound_assets = outboundAssets.map((asset) => ({
        ...asset,
        source: asset.source || 'explicit',
      }))
    }

    const userMessage: Message = {
      id: tempId,
      conversation_id: conversationId,
      role,
      content: content || file?.name || '',
      content_type: file?.type?.startsWith('image/')
        ? 'image'
        : file?.type?.startsWith('video/')
          ? 'video'
          : file
            ? 'file'
            : 'text',
      extra_data: Object.keys(extraData).length > 0 ? extraData : undefined,
      created_at: new Date().toISOString(),
    }

    set((state) => ({
      messages: [...state.messages, userMessage],
      isStreaming: shouldStream,
      streamingContent: shouldStream ? '' : state.streamingContent,
    }))

    try {
      if (file) {
        const form = new FormData()
        form.append('conversation_id', conversationId)
        form.append('file', file)
        form.append('role', role)
        if (content.trim()) {
          form.append('content', content.trim())
        }
        if (outboundAssets.length > 0) {
          form.append(
            'extraData',
            JSON.stringify({
              outbound_assets: outboundAssets.map((asset) => ({
                ...asset,
                source: asset.source || 'explicit',
              })),
            }),
          )
        }
        const saved = await api.upload<Message>('/chat/upload', form)
        const persisted = normalizeMessageMedia({
          ...saved,
          content_type: file.type?.startsWith('image/')
            ? 'image'
            : file.type?.startsWith('video/')
              ? 'video'
              : 'file',
        })
        set((state) => ({
          messages: state.messages.map((m) => (m.id === tempId ? persisted : m)),
        }))
        if (previewUrl) URL.revokeObjectURL(previewUrl)
      } else {
        const saved = await api.post<Message>('/chat/send', {
          conversation_id: conversationId,
          content,
          role,
          extra_data:
            outboundAssets.length > 0
              ? {
                  outbound_assets: outboundAssets.map((asset) => ({
                    ...asset,
                    source: asset.source || 'explicit',
                  })),
                }
              : undefined,
        })
        const persisted = normalizeMessageMedia(saved)
        set((state) => ({
          messages: state.messages.map((m) => (m.id === tempId ? persisted : m)),
          isStreaming: shouldStream,
        }))
        // Safety timeout: force end stream after 45s regardless
        if (shouldStream) {
          const timerId = setTimeout(() => {
            const s = useChatStore.getState()
            if (s.isStreaming) {
              s.endStream()
            }
          }, 45000)
          // Store timer ID for cleanup (avoid memory leaks)
          set((state) => ({ ...state, _streamTimer: timerId as any }))
        }
      }
    } catch (apiErr: any) {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      set((state) => ({
        error: apiErr.message,
        isStreaming: false,
        messages: state.messages.filter((m) => m.id !== tempId),
      }))
    }
  },

  createConversation: async (title?: string) => {
    const conv = await api.post<Conversation>('/chat/conversations', { title })
    set((state) => ({
      conversations: [conv, ...state.conversations],
      currentConversation: conv,
    }))
    return conv
  },

  clearCurrentConversation: () => {
    set({
      currentConversation: null,
      messages: [],
      isStreaming: false,
      streamingContent: '',
    })
  },

  addMessage: (message: Message) => {
    const normalized = normalizeMessageMedia(message)
    set((state) => {
      if (state.messages.some((m) => m.id === normalized.id)) {
        return { isStreaming: false, streamingContent: '' }
      }
      const duplicateAssistant =
        normalized.role === 'assistant' &&
        state.messages.some(
          (m) =>
            m.role === 'assistant' &&
            m.content === normalized.content &&
            m.conversation_id === normalized.conversation_id,
        )
      if (duplicateAssistant) {
        return { isStreaming: false, streamingContent: '' }
      }
      return {
        messages: [...state.messages, normalized],
        isStreaming: false,
        streamingContent: '',
      }
    })
  },

  appendToStream: (content: string) => {
    set((state) => ({
      streamingContent: state.streamingContent + content,
    }))
  },

  endStream: () => {
    set({ isStreaming: false, streamingContent: '' })
  },

  setError: (error: string | null) => set({ error }),
}))
