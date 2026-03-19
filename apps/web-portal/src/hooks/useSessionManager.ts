'use client'

import { useState, useCallback, useEffect } from 'react'

export interface ChatSessionItem {
  id: string
  title: string
  agentId: string | null
  messageCount: number
  createdAt: string
  updatedAt: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  thinking?: unknown
  toolCalls?: unknown
  createdAt: string
}

interface UseSessionManagerReturn {
  sessions: ChatSessionItem[]
  currentSessionId: string | null
  currentMessages: ChatMessage[]
  loading: boolean
  messagesLoading: boolean
  createSession: (title?: string) => Promise<ChatSessionItem | null>
  deleteSession: (id: string) => Promise<void>
  renameSession: (id: string, title: string) => Promise<void>
  selectSession: (id: string) => Promise<void>
  refreshSessions: () => Promise<void>
  saveMessages: (sessionId: string, messages: Array<{ role: string; content: string; thinking?: string; toolCalls?: unknown; tokens?: number; latencyMs?: number }>) => Promise<void>
}

export function useSessionManager(): UseSessionManagerReturn {
  const [sessions, setSessions] = useState<ChatSessionItem[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [currentMessages, setCurrentMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [messagesLoading, setMessagesLoading] = useState(false)

  // 加载会话列表
  const refreshSessions = useCallback(async () => {
    try {
      const res = await fetch('/api/chat/sessions', { credentials: 'include' })
      const data = (await res.json()) as { success: boolean; sessions: ChatSessionItem[] }
      if (data.success) {
        setSessions(data.sessions)
      }
    } catch {
      console.error('[sessions] refresh failed')
    } finally {
      setLoading(false)
    }
  }, [])

  // 初始化加载
  useEffect(() => {
    void refreshSessions()
  }, [refreshSessions])

  // 创建新会话
  const createSession = useCallback(async (title?: string): Promise<ChatSessionItem | null> => {
    try {
      const res = await fetch('/api/chat/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title }),
      })
      const data = (await res.json()) as { success: boolean; session: ChatSessionItem }
      if (data.success) {
        setSessions((prev) => [data.session, ...prev])
        setCurrentSessionId(data.session.id)
        setCurrentMessages([])
        return data.session
      }
    } catch {
      console.error('[sessions] create failed')
    }
    return null
  }, [])

  // 删除会话
  const deleteSession = useCallback(async (id: string) => {
    try {
      await fetch(`/api/chat/sessions/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      })
      setSessions((prev) => prev.filter((s) => s.id !== id))
      if (currentSessionId === id) {
        setCurrentSessionId(null)
        setCurrentMessages([])
      }
    } catch {
      console.error('[sessions] delete failed')
    }
  }, [currentSessionId])

  // 重命名会话
  const renameSession = useCallback(async (id: string, title: string) => {
    try {
      await fetch(`/api/chat/sessions/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title }),
      })
      setSessions((prev) =>
        prev.map((s) => (s.id === id ? { ...s, title } : s)),
      )
    } catch {
      console.error('[sessions] rename failed')
    }
  }, [])

  // 选择会话 (加载消息)
  const selectSession = useCallback(async (id: string) => {
    setCurrentSessionId(id)
    setMessagesLoading(true)
    try {
      const res = await fetch(`/api/chat/sessions/${id}`, { credentials: 'include' })
      const data = (await res.json()) as { success: boolean; session: { messages: ChatMessage[] } }
      if (data.success) {
        setCurrentMessages(data.session.messages)
      }
    } catch {
      console.error('[sessions] load messages failed')
    } finally {
      setMessagesLoading(false)
    }
  }, [])

  // 保存消息到 DB
  const saveMessages = useCallback(async (
    sessionId: string,
    messages: Array<{ role: string; content: string; thinking?: string; toolCalls?: unknown; tokens?: number; latencyMs?: number }>,
  ) => {
    try {
      await fetch('/api/chat/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ sessionId, messages }),
      })
      // 更新会话列表中的 title (如果首条消息触发了自动标题)
      void refreshSessions()
    } catch {
      console.error('[sessions] save messages failed')
    }
  }, [refreshSessions])

  return {
    sessions,
    currentSessionId,
    currentMessages,
    loading,
    messagesLoading,
    createSession,
    deleteSession,
    renameSession,
    selectSession,
    refreshSessions,
    saveMessages,
  }
}
