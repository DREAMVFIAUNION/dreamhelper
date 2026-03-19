'use client'

import { useEffect, useRef, useCallback, type ReactNode } from 'react'
import './electric-border.css'

interface ElectricBorderProps {
  children?: ReactNode
  color?: string
  speed?: number
  chaos?: number
  borderRadius?: number
  className?: string
}

export function ElectricBorder({
  children,
  color = 'hsl(var(--primary))',
  speed = 1,
  chaos = 0.12,
  borderRadius = 12,
  className = '',
}: ElectricBorderProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const animationRef = useRef<number>(0)
  const timeRef = useRef(0)
  const lastFrameRef = useRef(0)

  const random = useCallback((x: number) => {
    return (Math.sin(x * 12.9898) * 43758.5453) % 1
  }, [])

  const noise2D = useCallback((x: number, y: number) => {
    const i = Math.floor(x)
    const j = Math.floor(y)
    const fx = x - i
    const fy = y - j
    const a = random(i + j * 57)
    const b = random(i + 1 + j * 57)
    const c = random(i + (j + 1) * 57)
    const d = random(i + 1 + (j + 1) * 57)
    const ux = fx * fx * (3.0 - 2.0 * fx)
    const uy = fy * fy * (3.0 - 2.0 * fy)
    return a * (1 - ux) * (1 - uy) + b * ux * (1 - uy) + c * (1 - ux) * uy + d * ux * uy
  }, [random])

  const octavedNoise = useCallback(
    (x: number, octaves: number, lac: number, gain: number, amp: number, freq: number, time: number, seed: number, flat: number) => {
      let y = 0
      let amplitude = amp
      let frequency = freq
      for (let i = 0; i < octaves; i++) {
        let oa = amplitude
        if (i === 0) oa *= flat
        y += oa * noise2D(frequency * x + seed * 100, time * frequency * 0.3)
        frequency *= lac
        amplitude *= gain
      }
      return y
    },
    [noise2D],
  )

  const getRoundedRectPoint = useCallback(
    (t: number, left: number, top: number, w: number, h: number, r: number) => {
      const sw = w - 2 * r
      const sh = h - 2 * r
      const ca = (Math.PI * r) / 2
      const total = 2 * sw + 2 * sh + 4 * ca
      const d = t * total
      let acc = 0

      if (d <= acc + sw) {
        const p = (d - acc) / sw
        return { x: left + r + p * sw, y: top }
      }
      acc += sw

      if (d <= acc + ca) {
        const p = (d - acc) / ca
        const angle = -Math.PI / 2 + p * (Math.PI / 2)
        return { x: left + w - r + r * Math.cos(angle), y: top + r + r * Math.sin(angle) }
      }
      acc += ca

      if (d <= acc + sh) {
        const p = (d - acc) / sh
        return { x: left + w, y: top + r + p * sh }
      }
      acc += sh

      if (d <= acc + ca) {
        const p = (d - acc) / ca
        const angle = p * (Math.PI / 2)
        return { x: left + w - r + r * Math.cos(angle), y: top + h - r + r * Math.sin(angle) }
      }
      acc += ca

      if (d <= acc + sw) {
        const p = (d - acc) / sw
        return { x: left + w - r - p * sw, y: top + h }
      }
      acc += sw

      if (d <= acc + ca) {
        const p = (d - acc) / ca
        const angle = Math.PI / 2 + p * (Math.PI / 2)
        return { x: left + r + r * Math.cos(angle), y: top + h - r + r * Math.sin(angle) }
      }
      acc += ca

      if (d <= acc + sh) {
        const p = (d - acc) / sh
        return { x: left, y: top + h - r - p * sh }
      }
      acc += sh

      const p = (d - acc) / ca
      const angle = Math.PI + p * (Math.PI / 2)
      return { x: left + r + r * Math.cos(angle), y: top + r + r * Math.sin(angle) }
    },
    [],
  )

  useEffect(() => {
    const canvas = canvasRef.current
    const container = containerRef.current
    if (!canvas || !container) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const borderOffset = 60

    const updateSize = () => {
      const rect = container.getBoundingClientRect()
      const w = rect.width + borderOffset * 2
      const h = rect.height + borderOffset * 2
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = w * dpr
      canvas.height = h * dpr
      canvas.style.width = `${w}px`
      canvas.style.height = `${h}px`
      ctx.scale(dpr, dpr)
      return { width: w, height: h }
    }

    let { width, height } = updateSize()

    const draw = (currentTime: number) => {
      if (!canvas || !ctx) return
      const dt = (currentTime - lastFrameRef.current) / 1000
      timeRef.current += dt * speed
      lastFrameRef.current = currentTime

      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      ctx.setTransform(1, 0, 0, 1, 0, 0)
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.scale(dpr, dpr)

      ctx.strokeStyle = color
      ctx.lineWidth = 1
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'

      const bw = width - 2 * borderOffset
      const bh = height - 2 * borderOffset
      const maxR = Math.min(bw, bh) / 2
      const r = Math.min(borderRadius, maxR)

      const perim = 2 * (bw + bh) + 2 * Math.PI * r
      const samples = Math.floor(perim / 2)

      ctx.beginPath()
      for (let i = 0; i <= samples; i++) {
        const prog = i / samples
        const pt = getRoundedRectPoint(prog, borderOffset, borderOffset, bw, bh, r)
        const xn = octavedNoise(prog * 8, 10, 1.6, 0.7, chaos, 10, timeRef.current, 0, 0)
        const yn = octavedNoise(prog * 8, 10, 1.6, 0.7, chaos, 10, timeRef.current, 1, 0)
        const dx = pt.x + xn * 60
        const dy = pt.y + yn * 60
        if (i === 0) ctx.moveTo(dx, dy)
        else ctx.lineTo(dx, dy)
      }
      ctx.closePath()
      ctx.stroke()

      animationRef.current = requestAnimationFrame(draw)
    }

    const ro = new ResizeObserver(() => {
      const s = updateSize()
      width = s.width
      height = s.height
    })
    ro.observe(container)

    animationRef.current = requestAnimationFrame(draw)

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
      ro.disconnect()
    }
  }, [color, speed, chaos, borderRadius, octavedNoise, getRoundedRectPoint])

  return (
    <div ref={containerRef} className={`electric-border ${className}`} style={{ borderRadius }}>
      <div className="eb-canvas-container">
        <canvas ref={canvasRef} className="eb-canvas" />
      </div>
      <div className="eb-layers">
        <div className="eb-glow-1" />
        <div className="eb-glow-2" />
        <div className="eb-background-glow" />
      </div>
      <div className="eb-content">{children}</div>
    </div>
  )
}
