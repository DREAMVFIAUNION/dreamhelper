'use client'

import { useEffect, useRef, useCallback, useState } from 'react'

interface UseWebSocketOptions {
  url?: string
  onMessage?: (event: MessageEvent) => void
  onOpen?: () => void
  onClose?: () => void
  reconnect?: boolean
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    url = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:3001',
    reconnect = true,
  } = options
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)

  const connect = useCallback(() => {
    const ws = new WebSocket(url)

    ws.onopen = () => {
      setConnected(true)
      options.onOpen?.()
    }

    ws.onmessage = (event) => {
      options.onMessage?.(event)
    }

    ws.onclose = () => {
      setConnected(false)
      options.onClose?.()
      if (reconnect) {
        setTimeout(connect, 3000)
      }
    }

    wsRef.current = ws
  }, [url, reconnect, options])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((data: string | object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [])

  return { connected, send }
}
