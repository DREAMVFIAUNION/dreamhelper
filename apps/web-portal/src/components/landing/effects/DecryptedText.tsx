'use client'

import { useEffect, useState, useRef } from 'react'
import { motion } from 'framer-motion'

interface DecryptedTextProps {
  text: string
  speed?: number
  maxIterations?: number
  sequential?: boolean
  characters?: string
  className?: string
  encryptedClassName?: string
  animateOn?: 'hover' | 'view' | 'both'
}

export function DecryptedText({
  text,
  speed = 50,
  maxIterations = 10,
  sequential = true,
  characters = '01アイウエオカキクケコ▓░▒█◆◇■□●○',
  className = '',
  encryptedClassName = '',
  animateOn = 'view',
}: DecryptedTextProps) {
  const [displayText, setDisplayText] = useState(text)
  const [isHovering, setIsHovering] = useState(false)
  const [isScrambling, setIsScrambling] = useState(false)
  const [revealedIndices, setRevealedIndices] = useState(new Set<number>())
  const [hasAnimated, setHasAnimated] = useState(false)
  const containerRef = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>
    let currentIteration = 0
    const availableChars = characters.split('')

    if (isHovering) {
      setIsScrambling(true)
      interval = setInterval(() => {
        setRevealedIndices(prev => {
          if (sequential) {
            if (prev.size < text.length) {
              const newRevealed = new Set(prev)
              newRevealed.add(prev.size)
              const shuffled = text.split('').map((char, i) => {
                if (char === ' ') return ' '
                if (newRevealed.has(i)) return text[i]
                return availableChars[Math.floor(Math.random() * availableChars.length)]
              }).join('')
              setDisplayText(shuffled)
              return newRevealed
            } else {
              clearInterval(interval)
              setIsScrambling(false)
              return prev
            }
          } else {
            const shuffled = text.split('').map((char, i) => {
              if (char === ' ') return ' '
              if (prev.has(i)) return text[i]
              return availableChars[Math.floor(Math.random() * availableChars.length)]
            }).join('')
            setDisplayText(shuffled)
            currentIteration++
            if (currentIteration >= maxIterations) {
              clearInterval(interval)
              setIsScrambling(false)
              setDisplayText(text)
            }
            return prev
          }
        })
      }, speed)
    } else {
      setDisplayText(text)
      setRevealedIndices(new Set())
      setIsScrambling(false)
    }

    return () => { if (interval) clearInterval(interval) }
  }, [isHovering, text, speed, maxIterations, sequential, characters])

  useEffect(() => {
    if (animateOn !== 'view' && animateOn !== 'both') return

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting && !hasAnimated) {
            setIsHovering(true)
            setHasAnimated(true)
          }
        })
      },
      { threshold: 0.1 }
    )

    const el = containerRef.current
    if (el) observer.observe(el)
    return () => { if (el) observer.unobserve(el) }
  }, [animateOn, hasAnimated])

  const hoverProps = (animateOn === 'hover' || animateOn === 'both')
    ? {
        onMouseEnter: () => setIsHovering(true),
        onMouseLeave: () => setIsHovering(false),
      }
    : {}

  return (
    <motion.span
      ref={containerRef}
      style={{ display: 'inline-block', whiteSpace: 'pre-wrap' }}
      {...hoverProps}
    >
      <span className="sr-only">{displayText}</span>
      <span aria-hidden="true">
        {displayText.split('').map((char, index) => {
          const isRevealed = revealedIndices.has(index) || !isScrambling || !isHovering
          return (
            <span key={index} className={isRevealed ? className : (encryptedClassName || 'opacity-60')}>
              {char}
            </span>
          )
        })}
      </span>
    </motion.span>
  )
}
