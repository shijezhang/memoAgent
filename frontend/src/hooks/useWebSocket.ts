import { useState, useCallback, useRef, useEffect } from 'react'

interface UseWebSocketOptions {
  onMessage?: (text: string) => void
  onDone?: () => void
  onError?: (error: Event) => void
  reconnectDelay?: number
  maxReconnectAttempts?: number
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const shouldReconnectRef = useRef(true)

  const {
    reconnectDelay = 3000,
    maxReconnectAttempts = 5,
  } = options

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
      shouldReconnectRef.current = false
      reconnectTimeoutRef.current && clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close()
    }
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return wsRef.current
    }

    const wsUrl = `${window.location.origin.replace('http', 'ws')}/api/chat/ws`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setIsConnected(true)
      reconnectAttemptsRef.current = 0
    }

    ws.onmessage = (event) => {
      if (event.data === '[DONE]') {
        onDoneRef.current?.()
      } else {
        onMessageRef.current?.(event.data)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      onErrorRef.current?.(error)
    }

    ws.onclose = () => {
      setIsConnected(false)
      wsRef.current = null

      if (shouldReconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current++
        console.log(`Reconnecting... attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`)
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, reconnectDelay)
      }
    }

    wsRef.current = ws
    return ws
  }, [reconnectDelay, maxReconnectAttempts])

  const send = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message)
    } else {
      console.warn('WebSocket is not connected, attempting to reconnect...')
      connect()
    }
  }, [connect])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    reconnectTimeoutRef.current && clearTimeout(reconnectTimeoutRef.current)
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  return { isConnected, connect, send, disconnect, ws: wsRef }
}
