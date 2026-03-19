'use client'

import { useEffect, useRef, useCallback } from 'react'

// ── 文字池: 品牌词汇 + 希腊符号 + 数字 ──
const CHAR_POOL = [
  // 品牌
  ...'DREAMVFIA'.split(''),
  ...'梦帮集团'.split(''),
  ...'梦帮科技'.split(''),
  ...'梦帮文创'.split(''),
  ...'梦帮智能'.split(''),
  ...'梦帮宇宙'.split(''),
  // 希腊字母（小写）
  ...'αβγδεζηθικλμνξπρστφχψω'.split(''),
  // 希腊字母（大写）
  ...'ΣΔΩΦΨΛΘΞΠ'.split(''),
  // 数字
  ...'0123456789'.split(''),
]

interface MatrixRainProps {
  opacity?: number
  color?: string
  speed?: 'slow' | 'normal' | 'fast'
  density?: number
  className?: string
}

const SPEED_MAP = { slow: 50, normal: 33, fast: 20 }

export function MatrixRain({
  opacity = 0.15,
  color = '#FE0000',
  speed = 'normal',
  density = 1.0,
  className = '',
}: MatrixRainProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animRef = useRef<number>(0)
  const dropsRef = useRef<number[]>([])
  const lastFrameRef = useRef<number>(0)
  const pausedRef = useRef(false)

  // 随机取字符
  const randomChar = useCallback(() => {
    return CHAR_POOL[Math.floor(Math.random() * CHAR_POOL.length)]!
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const fontSize = 14
    const interval = SPEED_MAP[speed]
    let cols = 0
    let canvasW = 0
    let canvasH = 0

    // ── 绘制一帧 ──
    const drawFrame = () => {
      if (cols <= 0 || canvasW <= 0) return
      const colSpacing = canvasW / cols

      // 半透明黑色覆盖 → 产生拖尾淡出
      ctx.fillStyle = 'rgba(8, 8, 8, 0.12)'
      ctx.fillRect(0, 0, canvasW, canvasH)

      ctx.font = `${fontSize}px "JetBrains Mono", "Noto Sans SC", monospace`

      const drops = dropsRef.current
      for (let i = 0; i < cols; i++) {
        const char = randomChar()
        const x = i * colSpacing
        const y = drops[i]! * fontSize

        // 头部字符：高亮
        ctx.fillStyle = color
        ctx.globalAlpha = 0.9
        ctx.fillText(char, x, y)

        // 次亮字符（上一格）
        ctx.globalAlpha = 0.4
        ctx.fillText(randomChar(), x, y - fontSize)

        // 更暗的拖尾
        ctx.globalAlpha = 0.15
        ctx.fillText(randomChar(), x, y - fontSize * 2)

        ctx.globalAlpha = 1

        // 列到底后随机概率重置
        if (y > canvasH && Math.random() > 0.975) {
          drops[i] = 0
        }
        drops[i]! += 1
      }
    }

    // ── 尺寸 & 列初始化 ──
    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width * dpr
      canvas.height = rect.height * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

      canvasW = rect.width
      canvasH = rect.height

      // 移动端自动降密度
      const isMobile = rect.width < 768
      const effectiveDensity = density * (isMobile ? 0.5 : 1.0)
      const newCols = Math.floor((rect.width / fontSize) * effectiveDensity)

      // 保留已有列的 y 坐标，新增列随机初始化
      const oldDrops = dropsRef.current
      const newDrops = new Array(newCols)
      for (let i = 0; i < newCols; i++) {
        newDrops[i] = i < oldDrops.length
          ? oldDrops[i]!
          : -Math.random() * (rect.height / fontSize)
      }
      dropsRef.current = newDrops
      cols = newCols
    }

    resize()

    // ── prefers-reduced-motion ──
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    if (motionQuery.matches) {
      drawFrame()
      return
    }

    // ── ResizeObserver ──
    const ro = new ResizeObserver(resize)
    ro.observe(canvas)

    // ── Intersection Observer: 视口外暂停 ──
    const io = new IntersectionObserver(
      ([entry]) => { pausedRef.current = !entry!.isIntersecting },
      { threshold: 0 },
    )
    io.observe(canvas)

    // ── 动画循环 ──
    const loop = (timestamp: number) => {
      animRef.current = requestAnimationFrame(loop)

      if (pausedRef.current) return
      if (timestamp - lastFrameRef.current < interval) return
      lastFrameRef.current = timestamp

      drawFrame()
    }

    animRef.current = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(animRef.current)
      ro.disconnect()
      io.disconnect()
    }
  }, [opacity, color, speed, density, randomChar])

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full pointer-events-none ${className}`}
      style={{ opacity, willChange: 'transform' }}
    />
  )
}
