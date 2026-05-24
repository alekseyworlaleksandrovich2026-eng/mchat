import { useEffect, useCallback, useRef } from 'react'
import { useChatStore, Message } from '@/stores/chat'
import { getWsClient } from '@/lib/websocket'

export function useChat(conversationId?: string) {
  const {
    conversations,
    currentConversation,
    messages,
    isStreaming,
    streamingContent,
    isLoading,
    error,
    fetchConversations,
    fetchMessages,
    sendMessage,
    createConversation,
    addMessage,
    appendToStream,
    endStream,
    clearCurrentConversation,
    setError,
  } = useChatStore()

  const subscribedRef = useRef(false)

  const handleMessage = useCallback(
    (data: any) => {
      // Handle subscribed confirmation
      if (data.type === 'subscribed') {
        subscribedRef.current = true
        return
      }

      // Handle chat:stream (streaming AI tokens)
      if (data.type === 'chat:stream') {
        if (!data.conversation_id || data.conversation_id === conversationId) {
          appendToStream(data.content || '')
        }
        return
      }

      // Handle chat:stream:end (streaming complete)
      if (data.type === 'chat:stream:end') {
        if (!data.conversation_id || data.conversation_id === conversationId) {
          const existingContent = useChatStore.getState().streamingContent
          const exists = useChatStore.getState().messages.some(
            m => m.id === (data.id || '') && m.role === 'assistant'
          )
          if (!exists && (existingContent || data.content)) {
            const fullMessage: Message = {
              id: data.id || `msg-${Date.now()}`,
              conversation_id: data.conversation_id || conversationId || '',
              role: 'assistant',
              content: existingContent || data.content || '',
              content_type: 'text',
              created_at: new Date().toISOString(),
            }
            addMessage(fullMessage)
          } else {
            // Always end stream even if message already exists
            endStream()
          }
        }
        return
      }

      // Handle full messages (non-streaming) — skip if already have via streaming
      if (data.type === 'chat:message' || data.type === 'message') {
        const msg = data.message || data
        // Skip assistant messages for this conversation (they come via streaming)
        if (msg.role === 'assistant' && msg.conversation_id === conversationId) {
          return
        }
        const message: Message = {
          id: msg.id || `msg-${Date.now()}`,
          conversation_id: msg.conversation_id || conversationId || '',
          role: msg.role || 'assistant',
          content: msg.content || '',
          content_type: msg.content_type || 'text',
          extra_data: msg.extra_data,
          created_at: msg.created_at || new Date().toISOString(),
        }
        addMessage(message)
        return
      }

      // Handle errors
      if (data.type === 'chat:error') {
        setError(data.message || 'Error')
        endStream()
      }
    },
    [conversationId, addMessage, appendToStream, endStream, setError],
  )

  useEffect(() => {
    if (!conversationId) return

    subscribedRef.current = false

    // Load existing messages
    fetchMessages(conversationId)

    // Connect and subscribe to this conversation
    const ws = getWsClient()
    ws.connect()

    // Send subscribe after a short delay (let WS connect)
    const timer = setTimeout(() => {
      ws.send({ type: 'subscribe', conversation_id: conversationId })
    }, 300)

    const unsubscribe = ws.on('message', handleMessage)

    return () => {
      clearTimeout(timer)
      subscribedRef.current = false
      ws.send({ type: 'unsubscribe', conversation_id: conversationId })
      unsubscribe()
    }
  }, [conversationId, fetchMessages, handleMessage])



  return {
    conversations,
    currentConversation,
    messages,
    isStreaming,
    streamingContent,
    isLoading,
    error,
    sendMessage,
    createConversation,
    clearCurrentConversation,
    setError,
  }
}
