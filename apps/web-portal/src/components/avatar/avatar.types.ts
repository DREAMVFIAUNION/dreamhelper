import type { BrainPhase } from '@/hooks/useStreamChat'

export type AvatarState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'greeting' | 'error'

export type AvatarMode = 'floating' | 'sidebar' | 'hidden'

export interface AvatarSpriteProps {
  state: AvatarState
  size?: number
  className?: string
}

export interface AvatarPanelProps {
  brainPhase: BrainPhase
  isStreaming: boolean
  mode?: AvatarMode
  className?: string
}

export interface AvatarStatusBadgeProps {
  state: AvatarState
  brainPhase?: BrainPhase
}
