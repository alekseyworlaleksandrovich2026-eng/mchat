import { useCallback, useEffect, useState } from 'react'
import i18n from '@/i18n'
import type { Message } from '@/stores/chat'

const VISITOR_KEY_PREFIX = 'mchat_widget_visitor_'
const CONV_KEY_PREFIX = 'mchat_widget_conv_'

function visitorStorageKey(agentId: string) {
  return `${VISITOR_KEY_PREFIX}${agentId}`
}

function conversationStorageKey(agentId: string) {
  return `${CONV_KEY_PREFIX}${agentId}`
}

/** Stable per browser tab; cleared when tab closes — visitors do not share sessions. */
function getOrCreateVisitorToken(agentId: string): string {
  const key = visitorStorageKey(agentId)
  let token = sessionStorage.getItem(key)
  if (!token) {
    token =
      typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : `v_${Date.now()}_${Math.random().toString(36).slice(2)}`
    sessionStorage.setItem(key, token)
  }
  return token
}

/** Remove duplicate assistant replies (e.g. legacy double-save in DB). */
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

async function consumeWidgetStream(
  response: Response,
  onToken: (chunk: string, full: string) => void,
): Promise<{ conversationId: string; messageId: string; response: string }> {
  if (!response.body) {
    throw new Error('浏览器不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let full = ''
  let conversationId = ''
  let messageId = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data:')) continue
      const raw = line.slice(5).trim()
      if (!raw) continue
      const data = JSON.parse(raw) as {
        type: string
        content?: string
        conversationId?: string
        messageId?: string
        message?: string
      }

      if (data.type === 'token' && data.content) {
        full += data.content
        onToken(data.content, full)
      } else if (data.type === 'done') {
        conversationId = data.conversationId || conversationId
        messageId = data.messageId || messageId
        if (data.content) full = data.content
      } else if (data.type === 'error') {
        throw new Error(data.message || '流式请求失败')
      }
    }
  }

  return { conversationId, messageId, response: full }
}

export function useWidgetChat(agentId: string, apiUrl: string, welcomeMessage: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [historyLoading, setHistoryLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const base = apiUrl.replace(/\/$/, '')

  const loadHistory = useCallback(async () => {
    if (!agentId) return

    const visitorToken = getOrCreateVisitorToken(agentId)
    const convId = sessionStorage.getItem(conversationStorageKey(agentId))

    if (!convId) {
      setMessages([
        {
          id: 'welcome',
          conversation_id: '',
          role: 'assistant',
          content: welcomeMessage,
          content_type: 'text',
          created_at: new Date().toISOString(),
        },
      ])
      return
    }

    setHistoryLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ visitor_token: visitorToken })
      const res = await fetch(
        `${base}/widget/${agentId}/conversation/${convId}?${params}`,
      )
      if (!res.ok) {
        if (res.status === 404 || res.status === 403) {
          sessionStorage.removeItem(conversationStorageKey(agentId))
          setMessages([
            {
              id: 'welcome',
              conversation_id: '',
              role: 'assistant',
              content: welcomeMessage,
              content_type: 'text',
              created_at: new Date().toISOString(),
            },
          ])
          return
        }
        const body = await res.json().catch(() => ({}))
        throw new Error(
          typeof body.detail === 'string' ? body.detail : `加载历史失败 (${res.status})`,
        )
      }

      const data = await res.json()
      const list: Message[] = (data.messages || []).map((m: Message) => ({
        id: m.id,
        conversation_id: m.conversation_id,
        role: m.role as Message['role'],
        content: m.content,
        content_type: 'text' as const,
        created_at: m.created_at,
      }))

      if (list.length === 0) {
        setMessages([
          {
            id: 'welcome',
            conversation_id: convId,
            role: 'assistant',
            content: welcomeMessage,
            content_type: 'text',
            created_at: new Date().toISOString(),
          },
        ])
      } else {
        const filtered = list.filter(
          (m) => m.role === 'user' || m.role === 'assistant',
        )
        setMessages(dedupeMessages(filtered))
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载历史失败')
      setMessages([
        {
          id: 'welcome',
          conversation_id: '',
          role: 'assistant',
          content: welcomeMessage,
          content_type: 'text',
          created_at: new Date().toISOString(),
        },
      ])
    } finally {
      setHistoryLoading(false)
    }
  }, [agentId, base, welcomeMessage])

  useEffect(() => {
    if (!agentId) return
    loadHistory()
  }, [agentId, loadHistory])

  const sendMessage = useCallback(
    async (content: string) => {
      if (!agentId || !content.trim() || isLoading || isStreaming) return

      const visitorToken = getOrCreateVisitorToken(agentId)
      const text = content.trim()
      const tempId = `user-${Date.now()}`
      const userMessage: Message = {
        id: tempId,
        conversation_id: sessionStorage.getItem(conversationStorageKey(agentId)) || '',
        role: 'user',
        content: text,
        content_type: 'text',
        created_at: new Date().toISOString(),
      }

      setMessages((prev) => {
        const withoutWelcome = prev.filter((m) => m.id !== 'welcome')
        return [...withoutWelcome, userMessage]
      })
      setIsLoading(true)
      setIsStreaming(true)
      setStreamingContent('')
      setError(null)

      const convId = sessionStorage.getItem(conversationStorageKey(agentId))
      const payload = JSON.stringify({
        message: text,
        conversationId: convId,
        visitorToken,
      })

      try {
        let result: { conversationId: string; messageId: string; response: string }

        const streamRes = await fetch(`${base}/widget/${agentId}/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: payload,
        })

        if (streamRes.ok && streamRes.headers.get('content-type')?.includes('text/event-stream')) {
          result = await consumeWidgetStream(streamRes, (_chunk, full) => {
            setStreamingContent(full)
          })
        } else {
          const syncRes = await fetch(`${base}/widget/${agentId}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: payload,
          })
          if (!syncRes.ok) {
            const errBody = await syncRes.json().catch(() => ({}))
            throw new Error(
              typeof errBody.detail === 'string'
                ? errBody.detail
                : `请求失败 (${syncRes.status})`,
            )
          }
          const data = await syncRes.json()
          result = {
            conversationId: data.conversationId,
            messageId: data.messageId,
            response: data.response || '',
          }
          setStreamingContent(result.response)
        }

        if (result.conversationId) {
          sessionStorage.setItem(
            conversationStorageKey(agentId),
            result.conversationId,
          )
        }

        const assistantMessage: Message = {
          id: result.messageId || `assistant-${Date.now()}`,
          conversation_id: result.conversationId || convId || '',
          role: 'assistant',
          content: result.response || i18n.t('chat.fallbackResponse'),
          content_type: 'text',
          created_at: new Date().toISOString(),
        }

        setMessages((prev) =>
          dedupeMessages([
            ...prev.filter((m) => m.id !== tempId),
            userMessage,
            assistantMessage,
          ]),
        )
      } catch (e) {
        const errMsg = e instanceof Error ? e.message : i18n.t('chat.networkError')
        setError(errMsg)
        setMessages((prev) => [
          ...prev.filter((m) => m.id !== tempId),
          userMessage,
          {
            id: `error-${Date.now()}`,
            conversation_id: '',
            role: 'assistant',
            content: errMsg,
            content_type: 'text',
            created_at: new Date().toISOString(),
          },
        ])
      } finally {
        setIsLoading(false)
        setIsStreaming(false)
        setStreamingContent('')
      }
    },
    [agentId, base, isLoading, isStreaming],
  )

  return {
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    historyLoading,
    error,
    sendMessage,
    reloadHistory: loadHistory,
    setError,
  }
}
