'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import type { BrainPhase } from '@/hooks/useStreamChat'
import type { AvatarState } from './avatar.types'
import { PHASE_TO_AVATAR, GREETING_DURATION } from './avatar.config'

/**
 * 虚拟形象状态管理 hook
 * 将 brainPhase + isStreaming 转换为 AvatarState
 */
export function useAvatarState(brainPhase: BrainPhase, isStreaming: boolean) {
  const [avatarState, setAvatarState] = useState<AvatarState>('idle')
  const greetingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const prevStreamingRef = useRef(false)

  // brainPhase → avatarState
  useEffect(() => {
    const mapped = PHASE_TO_AVATAR[brainPhase] || 'idle'
    setAvatarState(mapped)

    // 清除之前的 greeting 定时器
    if (greetingTimerRef.current) {
      clearTimeout(greetingTimerRef.current)
      greetingTimerRef.current = null
    }
  }, [brainPhase])

  // streaming 结束时 → greeting → idle
  useEffect(() => {
    if (prevStreamingRef.current && !isStreaming) {
      setAvatarState('greeting')

      greetingTimerRef.current = setTimeout(() => {
        setAvatarState('idle')
        greetingTimerRef.current = null
      }, GREETING_DURATION)
    }
    prevStreamingRef.current = isStreaming
  }, [isStreaming])

  // streaming 开始 → listening
  useEffect(() => {
    if (isStreaming && avatarState === 'idle') {
      setAvatarState('listening')
    }
  }, [isStreaming, avatarState])

  // cleanup
  useEffect(() => {
    return () => {
      if (greetingTimerRef.current) clearTimeout(greetingTimerRef.current)
    }
  }, [])

  return avatarState
}
