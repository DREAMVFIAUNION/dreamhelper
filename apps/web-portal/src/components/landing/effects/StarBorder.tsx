'use client'

import { type ReactNode } from 'react'
import './star-border.css'

interface StarBorderProps {
  children: ReactNode
  className?: string
  color?: string
  speed?: string
  as?: 'button' | 'a' | 'div' | 'span'
}

export function StarBorder({
  children,
  className = '',
  color = 'hsl(var(--primary))',
  speed = '6s',
  as: Component = 'div',
}: StarBorderProps) {
  return (
    <Component className={`star-border-container ${className}`} style={{ padding: '1px 0' }}>
      <div
        className="star-border-gradient-bottom"
        style={{
          background: `radial-gradient(circle, ${color}, transparent 10%)`,
          animationDuration: speed,
        }}
      />
      <div
        className="star-border-gradient-top"
        style={{
          background: `radial-gradient(circle, ${color}, transparent 10%)`,
          animationDuration: speed,
        }}
      />
      <div className="star-border-inner">{children}</div>
    </Component>
  )
}
