'use client'

import { useEffect, useRef } from 'react'
import { animate, stagger } from 'animejs'
import { prefersReducedMotion } from './useAnime'

interface SplitTextRevealProps {
  text: string
  className?: string
  /** Tag to render */
  as?: 'h2' | 'h3' | 'p' | 'span'
  /** Delay per character in ms */
  charDelay?: number
}

export function SplitTextReveal({
  text,
  className = '',
  as: Tag = 'span',
  charDelay = 40,
}: SplitTextRevealProps) {
  const containerRef = useRef<HTMLElement>(null)
  const firedRef = useRef(false)

  useEffect(() => {
    if (!containerRef.current || prefersReducedMotion()) return

    const container = containerRef.current
    const chars = container.querySelectorAll('.split-char')
    if (chars.length === 0) return

    // Set initial state
    chars.forEach((el) => {
      ;(el as HTMLElement).style.opacity = '0'
      ;(el as HTMLElement).style.transform = 'translateY(20px) rotateX(90deg)'
    })

    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting && !firedRef.current) {
          firedRef.current = true
          animate(chars, {
            opacity: [0, 1],
            translateY: ['20px', '0px'],
            rotateX: ['90deg', '0deg'],
            duration: 500,
            delay: stagger(charDelay, { from: 'first' }),
            ease: 'easeOutBack',
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
  }, [text, charDelay])

  const chars = text.split('')

  return (
    <Tag
      ref={containerRef as React.RefObject<HTMLElement & HTMLHeadingElement & HTMLParagraphElement & HTMLSpanElement>}
      className={`inline-block ${className}`}
      style={{ perspective: '600px' }}
    >
      {chars.map((char, i) => (
        <span
          key={`${char}-${i}`}
          className="split-char inline-block"
          style={{ transformOrigin: 'bottom center' }}
        >
          {char === ' ' ? '\u00A0' : char}
        </span>
      ))}
    </Tag>
  )
}
