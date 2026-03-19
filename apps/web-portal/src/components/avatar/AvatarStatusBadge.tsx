'use client'

import type { AvatarStatusBadgeProps } from './avatar.types'
import { STATUS_TEXT, BRAIN_STATUS_TEXT } from './avatar.config'

export function AvatarStatusBadge({ state, brainPhase }: AvatarStatusBadgeProps) {
  const brainText = brainPhase ? BRAIN_STATUS_TEXT[brainPhase] : undefined
  const statusText = brainText || STATUS_TEXT[state]

  if (!statusText) return null

  return <div className="avatar-status-badge">{statusText}</div>
}
