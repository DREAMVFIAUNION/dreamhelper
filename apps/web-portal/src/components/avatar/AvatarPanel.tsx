'use client'

import type { AvatarPanelProps } from './avatar.types'
import { AvatarSprite } from './AvatarSprite'
import { AvatarStatusBadge } from './AvatarStatusBadge'
import { useAvatarState } from './useAvatarState'
import { DEFAULT_AVATAR_SIZE } from './avatar.config'
import './avatar.css'

export function AvatarPanel({
  brainPhase,
  isStreaming,
  mode = 'floating',
  className = '',
}: AvatarPanelProps) {
  const avatarState = useAvatarState(brainPhase, isStreaming)

  if (mode === 'hidden') return null

  const size = mode === 'floating' ? 160 : DEFAULT_AVATAR_SIZE
  const modeClass = mode === 'floating' ? 'avatar-panel-floating' : 'avatar-panel-sidebar'

  return (
    <div className={`${modeClass} ${className}`}>
      <AvatarSprite state={avatarState} size={size} />
      <AvatarStatusBadge state={avatarState} brainPhase={brainPhase} />
    </div>
  )
}
