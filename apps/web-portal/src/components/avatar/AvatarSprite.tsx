'use client'

import { useState, useEffect, useRef } from 'react'
import type { AvatarSpriteProps } from './avatar.types'
import { SPRITE_MAP, ANIMATION_MAP, DEFAULT_AVATAR_SIZE } from './avatar.config'

export function AvatarSprite({ state, size = DEFAULT_AVATAR_SIZE, className = '' }: AvatarSpriteProps) {
  const [currentSrc, setCurrentSrc] = useState(SPRITE_MAP[state])
  const [isTransitioning, setIsTransitioning] = useState(false)
  const prevStateRef = useRef(state)

  useEffect(() => {
    if (state === prevStateRef.current) return
    prevStateRef.current = state

    const newSrc = SPRITE_MAP[state]
    if (newSrc === currentSrc) return

    // 淡出 → 换图 → 淡入
    setIsTransitioning(true)
    const timer = setTimeout(() => {
      setCurrentSrc(newSrc)
      setIsTransitioning(false)
    }, 300)

    return () => clearTimeout(timer)
  }, [state, currentSrc])

  const animClass = ANIMATION_MAP[state] || ''
  const thinkingRing = state === 'thinking' ? 'avatar-thinking-ring' : ''

  return (
    <div
      className={`avatar-sprite-container ${thinkingRing} ${className}`}
      style={{ width: size, height: size }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={currentSrc}
        alt="梦帮小助"
        width={size}
        height={size}
        className={`avatar-sprite-image ${animClass} ${isTransitioning ? 'exiting' : ''}`}
        style={{ width: size, height: size, objectFit: 'contain' }}
        draggable={false}
      />
    </div>
  )
}
