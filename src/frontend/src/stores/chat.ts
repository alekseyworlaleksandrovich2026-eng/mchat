import { create } from 'zustand'
import api from '@/lib/api'

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
  role: 'user' | 'assistant' | 'system'
  content: string
  content_type?: 'text' | 'image' | 'file'
  extra_data?: Record<string, any>
  created_at: string
}

export interface Conversation {
  id: string
  title: string | null
  status: 'active' | 'waiting' | 'closed'
  visitor_id: string | null
  contact_info: string | null
  created_at: string
  updated_at: string
  last_seen_at: string
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
  sendMessage: (conversationId: string, content: string) => Promise<void>
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
        messages: dedupeMessages(resp.messages || []),
        isLoading: false,
      })
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
    }
  },

  sendMessage: async (conversationId: string, content: string) => {
    const tempId = `temp-${Date.now()}`

    const userMessage: Message = {
      id: tempId,
      conversation_id: conversationId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }

    set((state) => ({
      messages: [...state.messages, userMessage],
      isStreaming: true,
      streamingContent: '',
    }))

    try {
      await api.post('/chat/send', {
        conversation_id: conversationId,
        content,
        role: 'user',
      })
    } catch (apiErr: any) {
      set({ error: apiErr.message, isStreaming: false })
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
    set((state) => {
      if (state.messages.some((m) => m.id === message.id)) {
        return { isStreaming: false, streamingContent: '' }
      }
      const duplicateAssistant =
        message.role === 'assistant' &&
        state.messages.some(
          (m) =>
            m.role === 'assistant' &&
            m.content === message.content &&
            m.conversation_id === message.conversation_id,
        )
      if (duplicateAssistant) {
        return { isStreaming: false, streamingContent: '' }
      }
      return {
        messages: [...state.messages, message],
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
