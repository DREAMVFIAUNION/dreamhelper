'use client'

import { useEffect, useRef } from 'react'
import { animate, stagger, createTimeline } from 'animejs'
import { prefersReducedMotion } from './useAnime'

// ── 电路装饰线 (PCB 风格) ──
const CIRCUIT_LINES = [
  // 左侧
  { d: 'M140,82 L90,82 L60,72', w: 1, op: 0.5 },
  { d: 'M145,90 L100,90 L70,97', w: 0.7, op: 0.3 },
  // 右侧
  { d: 'M660,82 L710,82 L740,72', w: 1, op: 0.5 },
  { d: 'M655,90 L700,90 L730,97', w: 0.7, op: 0.3 },
]

// ── 端子圆点 ──
const TERMINALS = [
  { cx: 55, cy: 70, r: 2.2 },
  { cx: 65, cy: 97, r: 1.6 },
  { cx: 745, cy: 70, r: 2.2 },
  { cx: 735, cy: 97, r: 1.6 },
]

interface HeroBrandTextProps {
  className?: string
}

export function HeroBrandText({ className = '' }: HeroBrandTextProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || prefersReducedMotion()) return
    const svg = svgRef.current

    // ── 描边文字 dasharray 初始化 ──
    const strokeText = svg.querySelector<SVGTextElement>('.brand-stroke')
    if (strokeText) {
      const len = strokeText.getComputedTextLength()
      strokeText.style.strokeDasharray = `${len}`
      strokeText.style.strokeDashoffset = `${len}`
    }

    // ── 电路线 dasharray 初始化 ──
    svg.querySelectorAll<SVGPathElement>('.brand-circuit').forEach(path => {
      const len = path.getTotalLength()
      path.style.strokeDasharray = `${len}`
      path.style.strokeDashoffset = `${len}`
    })

    // ── Timeline 编排 ──
    const tl = createTimeline({
      defaults: { ease: 'easeOutExpo' },
    })

    // t=0: 方括号从两侧滑入
    tl.add('.brand-bracket-l', {
      translateX: ['-18px', '0px'],
      opacity: [0, 0.75],
      duration: 650,
    }, 0)
    tl.add('.brand-bracket-r', {
      translateX: ['18px', '0px'],
      opacity: [0, 0.75],
      duration: 650,
    }, 0)

    // t=150: 描边文字绘入
    tl.add('.brand-stroke', {
      strokeDashoffset: [0],
      opacity: [0, 1],
      duration: 1100,
      ease: 'easeInOutQuad',
    }, 150)

    // t=500: 扫描线横扫 + 填充文字揭露
    tl.add('.brand-reveal-rect', {
      width: ['0', '680'],
      duration: 850,
      ease: 'easeInOutCubic',
    }, 500)
    tl.add('.brand-scan-bar', {
      translateX: ['0px', '680px'],
      opacity: [0.9, 0],
      duration: 850,
      ease: 'easeInOutCubic',
    }, 500)

    // t=650: 电路线描边
    tl.add('.brand-circuit', {
      strokeDashoffset: [0],
      duration: 500,
      delay: stagger(70),
    }, 650)

    // t=850: 端子闪入
    tl.add('.brand-terminal', {
      opacity: [0, 0.6],
      scale: [0, 1],
      duration: 300,
      delay: stagger(40),
    }, 850)

    // t=900: 数据标签淡入
    tl.add('.brand-label', {
      opacity: [0, 0.5],
      duration: 450,
      delay: stagger(100),
    }, 900)

    // t=1100: 发光层淡入
    tl.add('.brand-glow', {
      opacity: [0, 0.4],
      duration: 650,
    }, 1100)

    // ── 永久循环 ──

    // 发光呼吸
    animate('.brand-glow', {
      opacity: [0.25, 0.6],
      duration: 3000,
      loop: true,
      alternate: true,
      ease: 'easeInOutSine',
    })

    // 微弱扫描线循环
    animate('.brand-scan-repeat', {
      translateX: ['-60px', '740px'],
      duration: 5000,
      loop: true,
      ease: 'linear',
    })

    // ONLINE 指示灯闪烁
    animate('.brand-online-dot', {
      opacity: [0.3, 0.9],
      duration: 1200,
      loop: true,
      alternate: true,
      ease: 'easeInOutSine',
    })

  }, [])

  // SVG 文字样式
  const textProps = {
    x: 400,
    y: 66,
    textAnchor: 'middle' as const,
    style: {
      fontFamily: 'Orbitron, sans-serif',
      fontSize: '54px',
      fontWeight: 900,
      letterSpacing: '0.25em',
    },
  }

  return (
    <div className={className}>
      <svg
        ref={svgRef}
        viewBox="0 0 800 115"
        className="w-full h-auto"
        style={{ filter: 'drop-shadow(0 0 8px hsl(var(--primary) / 0.15))' }}
      >
        <defs>
          {/* 发光模糊滤镜 */}
          <filter id="brandGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" />
          </filter>
          {/* 扫描揭露裁剪 */}
          <clipPath id="brandReveal">
            <rect className="brand-reveal-rect" x="60" y="0" width="0" height="115" />
          </clipPath>
        </defs>

        {/* ═══ 层1: 红色发光文字 ═══ */}
        <text
          className="brand-glow"
          {...textProps}
          fill="hsl(var(--primary))"
          opacity="0"
          filter="url(#brandGlow)"
        >
          DREAMVFIA
        </text>

        {/* ═══ 层2: 描边文字 (绘入动画) ═══ */}
        <text
          className="brand-stroke"
          {...textProps}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth="1.2"
          opacity="0"
        >
          DREAMVFIA
        </text>

        {/* ═══ 层3: 填充文字 (扫描揭露) ═══ */}
        <g clipPath="url(#brandReveal)">
          <text
            {...textProps}
            fill="white"
          >
            DREAMVFIA
          </text>
        </g>

        {/* ═══ 扫描竖线 (入场) ═══ */}
        <rect
          className="brand-scan-bar"
          x="60" y="12" width="3" height="75"
          fill="hsl(var(--primary))"
          opacity="0"
          rx="1.5"
          style={{ filter: 'blur(1.5px)' }}
        />

        {/* ═══ 微弱循环扫描线 ═══ */}
        <rect
          className="brand-scan-repeat"
          x="0" y="18" width="1.5" height="65"
          fill="hsl(var(--primary))"
          opacity="0.06"
          rx="0.75"
        />

        {/* ═══ 方括号框架 ═══ */}
        <text
          className="brand-bracket-l"
          x="58" y="68"
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth="1.5"
          opacity="0"
          style={{ fontFamily: 'Orbitron, sans-serif', fontSize: '52px', fontWeight: 300 }}
        >
          [
        </text>
        <text
          className="brand-bracket-r"
          x="722" y="68"
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth="1.5"
          opacity="0"
          style={{ fontFamily: 'Orbitron, sans-serif', fontSize: '52px', fontWeight: 300 }}
        >
          ]
        </text>

        {/* ═══ 电路装饰线 ═══ */}
        {CIRCUIT_LINES.map((c, i) => (
          <path
            key={`bc-${i}`}
            className="brand-circuit"
            d={c.d}
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth={c.w}
            opacity={c.op}
            strokeLinecap="round"
          />
        ))}

        {/* ═══ 端子圆点 ═══ */}
        {TERMINALS.map((t, i) => (
          <circle
            key={`bt-${i}`}
            className="brand-terminal"
            cx={t.cx} cy={t.cy} r={t.r}
            fill="hsl(var(--primary))"
            opacity="0"
            style={{ transformOrigin: `${t.cx}px ${t.cy}px` }}
          />
        ))}

        {/* ═══ 数据标签 ═══ */}
        <text
          className="brand-label"
          x="52" y="112"
          fill="hsl(var(--primary))"
          opacity="0"
          style={{ fontFamily: 'monospace', fontSize: '8px' }}
        >
          v3.1.0
        </text>
        <g className="brand-label" opacity="0">
          <text
            x="740" y="112"
            fill="hsl(var(--primary))"
            textAnchor="end"
            style={{ fontFamily: 'monospace', fontSize: '8px' }}
          >
            ONLINE
          </text>
          <circle
            className="brand-online-dot"
            cx="745" cy="109" r="2.5"
            fill="hsl(var(--primary))"
            opacity="0.5"
            style={{ filter: 'blur(0.5px)' }}
          />
        </g>
      </svg>
    </div>
  )
}
