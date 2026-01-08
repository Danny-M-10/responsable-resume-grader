/**
 * WebSocket client for real-time progress updates
 */
export class ProgressWebSocket {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private onProgressCallback?: (data: any) => void
  private onErrorCallback?: (error: Event) => void
  private onCloseCallback?: () => void

  constructor(clientId: string = "default") {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.hostname
    // In production, use same host/port; in dev, use port 8000
    const wsPort = import.meta.env.PROD ? window.location.port : (import.meta.env.VITE_WS_PORT || '8000')
    const portSuffix = wsPort ? `:${wsPort}` : ''
    this.url = `${wsProtocol}//${wsHost}${portSuffix}/ws/progress?client_id=${clientId}`
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'progress' && this.onProgressCallback) {
            this.onProgressCallback(data)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        if (this.onErrorCallback) {
          this.onErrorCallback(error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        if (this.onCloseCallback) {
          this.onCloseCallback()
        }
        this.attemptReconnect()
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
        this.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }

  onProgress(callback: (data: any) => void) {
    this.onProgressCallback = callback
  }

  onError(callback: (error: Event) => void) {
    this.onErrorCallback = callback
  }

  onClose(callback: () => void) {
    this.onCloseCallback = callback
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

