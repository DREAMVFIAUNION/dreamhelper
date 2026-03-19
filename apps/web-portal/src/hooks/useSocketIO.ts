'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

export interface SocketNotification {
  type: string
  title: string
  content: string
  timestamp: number
}

interface UseSocketIOOptions {
  url?: string
  namespace?: string
  userId?: string
  enabled?: boolean
  onNotification?: (notification: SocketNotification) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

export function useSocketIO(options: UseSocketIOOptions = {}) {
  const {
    url = process.env.NEXT_PUBLIC_WS_URL ?? 'http://localhost:3001',
    namespace = '/ws',
    userId,
    enabled = true,
  } = options

  const socketRef = useRef<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [notifications, setNotifications] = useState<SocketNotification[]>([])

  useEffect(() => {
    if (!enabled || !userId) return

    const socket = io(`${url}${namespace}`, {
      query: { userId },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 3000,
      reconnectionAttempts: 10,
    })

    socket.on('connect', () => {
      setConnected(true)
      options.onConnect?.()
      console.log('[Socket.IO] Connected:', socket.id)
    })

    socket.on('disconnect', () => {
      setConnected(false)
      options.onDisconnect?.()
      console.log('[Socket.IO] Disconnected')
    })

    // 主动唤醒消息
    socket.on('proactive:message', (data: SocketNotification) => {
      setNotifications((prev) => [...prev, data])
      options.onNotification?.(data)
    })

    // 通用通知
    socket.on('notification', (data: SocketNotification) => {
      setNotifications((prev) => [...prev, data])
      options.onNotification?.(data)
    })

    socketRef.current = socket

    return () => {
      socket.disconnect()
      socketRef.current = null
    }
  }, [url, namespace, userId, enabled]) // eslint-disable-line react-hooks/exhaustive-deps

  const emit = useCallback((event: string, data: unknown) => {
    socketRef.current?.emit(event, data)
  }, [])

  const joinSession = useCallback((sessionId: string) => {
    socketRef.current?.emit('chat:join', { sessionId })
  }, [])

  const dismissNotification = useCallback((index: number) => {
    setNotifications((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const dismissAll = useCallback(() => {
    setNotifications([])
  }, [])

  return {
    connected,
    notifications,
    emit,
    joinSession,
    dismissNotification,
    dismissAll,
  }
}
