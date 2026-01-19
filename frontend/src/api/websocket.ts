/**
 * WebSocket client for real-time progress updates
 */
export class ProgressWebSocket {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private shouldReconnect = true
  private onProgressCallback?: (data: any) => void
  private onErrorCallback?: (error: Event) => void
  private onCloseCallback?: () => void

  constructor(clientId: string = "default") {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.hostname
    
    // Determine WebSocket port:
    // 1. If VITE_WS_PORT is explicitly set, use it (works for all environments)
    // 2. In development, default to backend port 8000
    // 3. In production, use window.location.port if non-empty (same port as frontend)
    //    If window.location.port is empty (default ports 80/443), assume same port as frontend
    //    (reverse proxy/load balancer scenario) - no port suffix needed
    let wsPort: string | undefined
    if (import.meta.env.VITE_WS_PORT) {
      wsPort = import.meta.env.VITE_WS_PORT
    } else if (import.meta.env.PROD) {
      // In production: use window.location.port if available, otherwise assume same port as frontend
      wsPort = window.location.port || undefined
    } else {
      // In development: default to backend port 8000
      wsPort = '8000'
    }
    
    // Only include port suffix if we have a specific port (and it's not default)
    // Empty string means default port, which should not include :port in the URL
    const portSuffix = wsPort ? `:${wsPort}` : ''
    this.url = `${wsProtocol}//${wsHost}${portSuffix}/ws/progress?client_id=${clientId}`
  }

  connect() {
    this.shouldReconnect = true
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
        if (this.shouldReconnect) {
          this.attemptReconnect()
        }
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
    this.shouldReconnect = false
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

