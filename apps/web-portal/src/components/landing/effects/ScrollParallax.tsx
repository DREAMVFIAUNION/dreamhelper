'use client'

import { useEffect, useRef, type ReactNode } from 'react'
import { prefersReducedMotion } from './useAnime'

interface ScrollParallaxProps {
  children: ReactNode
  /** Y offset range in px: element moves from -offset to +offset */
  offsetY?: number
  /** Scale range: [min, max] */
  scaleRange?: [number, number]
  /** Opacity range: [min, max] */
  opacityRange?: [number, number]
  className?: string
}

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t
}

export function ScrollParallax({
  children,
  offsetY = 40,
  scaleRange,
  opacityRange,
  className = '',
}: ScrollParallaxProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current || prefersReducedMotion()) return

    const el = containerRef.current
    let rafId = 0

    const update = () => {
      const rect = el.getBoundingClientRect()
      const vh = window.innerHeight
      // progress: 0 when element enters bottom, 1 when leaves top
      const progress = Math.max(0, Math.min(1, 1 - (rect.top + rect.height) / (vh + rect.height)))

      const transforms: string[] = []
      let opacity = ''

      if (offsetY) {
        const y = lerp(-offsetY, offsetY, progress)
        transforms.push(`translateY(${y.toFixed(1)}px)`)
      }
      if (scaleRange) {
        const s = lerp(scaleRange[0], scaleRange[1], progress)
        transforms.push(`scale(${s.toFixed(3)})`)
      }
      if (opacityRange) {
        opacity = `${lerp(opacityRange[0], opacityRange[1], progress).toFixed(2)}`
      }

      if (transforms.length) el.style.transform = transforms.join(' ')
      if (opacity) el.style.opacity = opacity
    }

    const onScroll = () => {
      cancelAnimationFrame(rafId)
      rafId = requestAnimationFrame(update)
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    update()

    return () => {
      window.removeEventListener('scroll', onScroll)
      cancelAnimationFrame(rafId)
    }
  }, [offsetY, scaleRange, opacityRange])

  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  )
}
