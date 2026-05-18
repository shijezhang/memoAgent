import { useState, useCallback, useRef } from 'react'

interface UseWebSocketOptions {
  onMessage?: (text: string) => void
  onDone?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    const wsUrl = `${window.location.origin.replace('http', 'ws')}/api/chat/ws`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      if (event.data === '[DONE]') {
        options.onDone?.()
      } else {
        options.onMessage?.(event.data)
      }
    }

    ws.onerror = (error) => {
      options.onError?.(error)
    }

    ws.onclose = () => {
      setIsConnected(false)
    }

    wsRef.current = ws
    return ws
  }, [options])

  const send = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message)
    }
  }, [])

  const disconnect = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  return { isConnected, connect, send, disconnect, ws: wsRef }
}
