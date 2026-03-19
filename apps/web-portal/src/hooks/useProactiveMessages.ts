'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

export interface ProactiveMessage {
  trigger: string
  title: string
  content: string
  created_at: number
}

interface UseProactiveOptions {
  userId?: string
  pollInterval?: number  // ms
  enabled?: boolean
}

export function useProactiveMessages(options: UseProactiveOptions = {}) {
  const {
    userId = 'anonymous',
    pollInterval = 15000,
    enabled = true,
  } = options

  const [messages, setMessages] = useState<ProactiveMessage[]>([])
  const [hasNew, setHasNew] = useState(false)
  const heartbeatSent = useRef(false)

  // 上线心跳
  useEffect(() => {
    if (!enabled || heartbeatSent.current) return
    heartbeatSent.current = true
    fetch('/api/proactive/heartbeat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, action: 'online' }),
    }).catch(() => {})

    return () => {
      fetch('/api/proactive/heartbeat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, action: 'offline' }),
      }).catch(() => {})
    }
  }, [userId, enabled])

  // 定期轮询主动消息
  useEffect(() => {
    if (!enabled) return

    const poll = async () => {
      try {
        const res = await fetch(`/api/proactive/messages?user_id=${userId}`)
        const data = await res.json()
        if (data.messages && data.messages.length > 0) {
          setMessages((prev) => [...prev, ...data.messages])
          setHasNew(true)
        }
      } catch {}
    }

    const timer = setInterval(poll, pollInterval)
    // 首次延迟 3 秒后轮询
    const initial = setTimeout(poll, 3000)

    return () => {
      clearInterval(timer)
      clearTimeout(initial)
    }
  }, [userId, pollInterval, enabled])

  const dismiss = useCallback((index: number) => {
    setMessages((prev) => prev.filter((_, i) => i !== index))
    setHasNew(false)
  }, [])

  const dismissAll = useCallback(() => {
    setMessages([])
    setHasNew(false)
  }, [])

  return { messages, hasNew, dismiss, dismissAll }
}
