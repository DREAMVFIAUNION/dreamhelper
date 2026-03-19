'use client'

import { useEffect, useRef, type ReactNode } from 'react'
import { animate, stagger } from 'animejs'
import { prefersReducedMotion } from './useAnime'

interface StaggerGridProps {
  children: ReactNode
  /** CSS selector for child items to animate */
  itemSelector?: string
  /** Grid columns for stagger grid calculation */
  cols?: number
  /** Grid rows for stagger grid calculation */
  rows?: number
  /** Stagger origin: 'center' | 'first' | 'last' | number */
  from?: 'center' | 'first' | 'last' | number
  /** Base delay per item in ms */
  baseDelay?: number
  className?: string
}

export function StaggerGrid({
  children,
  itemSelector = '[data-stagger-item]',
  cols = 3,
  rows = 2,
  from = 'center',
  baseDelay = 80,
  className = '',
}: StaggerGridProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const firedRef = useRef(false)

  useEffect(() => {
    if (!containerRef.current || prefersReducedMotion()) return

    const container = containerRef.current
    const items = container.querySelectorAll(itemSelector)
    if (items.length === 0) return

    // Set initial state
    items.forEach((el) => {
      ;(el as HTMLElement).style.opacity = '0'
      ;(el as HTMLElement).style.transform = 'translateY(30px) scale(0.95)'
    })

    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting && !firedRef.current) {
          firedRef.current = true
          animate(items, {
            opacity: [0, 1],
            translateY: ['30px', '0px'],
            scale: [0.95, 1],
            duration: 600,
            delay: stagger(baseDelay, {
              grid: [cols, rows],
              from,
            }),
            ease: 'easeOutQuint',
          })
          io.disconnect()
        }
      },
      { threshold: 0.1 },
    )

    io.observe(container)

    return () => {
      io.disconnect()
    }
  }, [itemSelector, cols, rows, from, baseDelay])

  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  )
}
