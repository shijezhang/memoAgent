import { useState, useCallback, useRef, useEffect } from 'react'

interface UseWebSocketOptions {
  onMessage?: (text: string) => void
  onDone?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const onMessageRef = useRef(options.onMessage)
  const onDoneRef = useRef(options.onDone)
  const onErrorRef = useRef(options.onError)

  useEffect(() => {
    onMessageRef.current = options.onMessage
    onDoneRef.current = options.onDone
    onErrorRef.current = options.onError
  }, [options.onMessage, options.onDone, options.onError])

  useEffect(() => {
    return () => {
      wsRef.current?.close()
    }
  }, [])

  const connect = useCallback(() => {
    const wsUrl = `${window.location.origin.replace('http', 'ws')}/api/chat/ws`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      if (event.data === '[DONE]') {
        onDoneRef.current?.()
      } else {
        onMessageRef.current?.(event.data)
      }
    }

    ws.onerror = (error) => {
      onErrorRef.current?.(error)
    }

    ws.onclose = () => {
      setIsConnected(false)
    }

    wsRef.current = ws
    return ws
  }, [])

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
