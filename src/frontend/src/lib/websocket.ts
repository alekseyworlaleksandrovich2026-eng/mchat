import { getToken } from './api'

type MessageHandler = (data: any) => void
type StatusHandler = (status: WebSocketStatus) => void

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting'

type EventMap = {
  message: MessageHandler
  status: StatusHandler
  [key: string]: any
}

class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private outboundQueue: unknown[] = []
  private handlers: Map<string, Set<Function>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectDelay = 1000
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private pingTimer: ReturnType<typeof setInterval> | null = null
  private status: WebSocketStatus = 'disconnected'

  constructor(url: string = '/ws') {
    this.url = url
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return

    this.setStatus('connecting')

    const token = getToken()
    const wsUrl = token
      ? `${this.url}?token=${encodeURIComponent(token)}`
      : this.url

    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        this.setStatus('connected')
        this.reconnectAttempts = 0
        this.flushOutboundQueue()
        this.startPing()
      }

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          this.emit('message', data)

          if (data.type) {
            this.emit(data.type, data)
          }
        } catch {
          this.emit('message', { type: 'raw', data: event.data })
        }
      }

      this.ws.onclose = () => {
        this.setStatus('disconnected')
        this.stopPing()
        this.scheduleReconnect()
      }

      this.ws.onerror = () => {
        this.ws?.close()
      }
    } catch {
      this.setStatus('disconnected')
      this.scheduleReconnect()
    }
  }

  disconnect(): void {
    this.reconnectAttempts = this.maxReconnectAttempts
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.stopPing()
    this.ws?.close()
    this.ws = null
    this.setStatus('disconnected')
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
      return
    }
    this.outboundQueue.push(data)
  }

  private flushOutboundQueue(): void {
    if (this.ws?.readyState !== WebSocket.OPEN) return
    while (this.outboundQueue.length > 0) {
      const data = this.outboundQueue.shift()
      this.ws.send(JSON.stringify(data))
    }
  }

  on(event: string, handler: Function): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set())
    }
    this.handlers.get(event)!.add(handler)

    return () => {
      this.handlers.get(event)?.delete(handler)
    }
  }

  off(event: string, handler: Function): void {
    this.handlers.get(event)?.delete(handler)
  }

  getStatus(): WebSocketStatus {
    return this.status
  }

  private emit(event: string, data: any): void {
    this.handlers.get(event)?.forEach((handler) => {
      try {
        handler(data)
      } catch (err) {
        console.error(`WebSocket handler error for event "${event}":`, err)
      }
    })
  }

  private setStatus(status: WebSocketStatus): void {
    this.status = status
    this.emit('status', status)
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return
    if (this.reconnectTimer) return

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      30000,
    )

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.reconnectAttempts++
      this.setStatus('reconnecting')
      this.connect()
    }, delay)
  }

  private startPing(): void {
    this.stopPing()
    this.pingTimer = setInterval(() => {
      this.send({ type: 'ping' })
    }, 30000)
  }

  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
  }
}

let wsClient: WebSocketClient | null = null

export function getWsClient(url?: string): WebSocketClient {
  if (!wsClient) {
    wsClient = new WebSocketClient(url)
  }
  return wsClient
}

export { WebSocketClient }
export default getWsClient
