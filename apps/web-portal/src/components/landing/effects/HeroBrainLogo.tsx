'use client'

import { useEffect, useRef } from 'react'
import Image from 'next/image'
import { animate, stagger, createTimeline } from 'animejs'
import { prefersReducedMotion } from './useAnime'

// ── SVG 齿轮路径生成 ──
function gearPath(cx: number, cy: number, r: number, teeth: number, toothDepth: number): string {
  const points: string[] = []
  const step = (Math.PI * 2) / (teeth * 2)
  for (let i = 0; i < teeth * 2; i++) {
    const angle = step * i - Math.PI / 2
    const radius = i % 2 === 0 ? r + toothDepth : r - toothDepth
    const x = cx + Math.cos(angle) * radius
    const y = cy + Math.sin(angle) * radius
    points.push(`${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`)
  }
  points.push('Z')
  return points.join(' ')
}

// ── 刻度线生成 (72个, 每5°) ──
function tickMarks(cx: number, cy: number, rInner: number, rOuter: number, count: number): string {
  const lines: string[] = []
  for (let i = 0; i < count; i++) {
    const angle = (Math.PI * 2 * i) / count - Math.PI / 2
    const isMajor = i % 6 === 0
    const inner = isMajor ? rInner - 3 : rInner
    const x1 = cx + Math.cos(angle) * inner
    const y1 = cy + Math.sin(angle) * inner
    const x2 = cx + Math.cos(angle) * rOuter
    const y2 = cy + Math.sin(angle) * rOuter
    lines.push(`M${x1.toFixed(1)},${y1.toFixed(1)}L${x2.toFixed(1)},${y2.toFixed(1)}`)
  }
  return lines.join(' ')
}

// ── 断裂弧线 (3段 ~100°每段, 中间断口) ──
function brokenArc(cx: number, cy: number, r: number): string[] {
  const arcs: string[] = []
  const segments = [
    { start: -20, end: 80 },
    { start: 100, end: 200 },
    { start: 220, end: 320 },
  ]
  for (const seg of segments) {
    const a1 = (seg.start * Math.PI) / 180
    const a2 = (seg.end * Math.PI) / 180
    const x1 = cx + Math.cos(a1) * r
    const y1 = cy + Math.sin(a1) * r
    const x2 = cx + Math.cos(a2) * r
    const y2 = cy + Math.sin(a2) * r
    arcs.push(`M${x1.toFixed(1)},${y1.toFixed(1)} A${r},${r} 0 0,1 ${x2.toFixed(1)},${y2.toFixed(1)}`)
  }
  return arcs
}

// ── 电路板线路路径 (带直角折弯) ──
const CIRCUIT_PATHS = [
  // 左上
  { d: 'M160,160 L120,120 L80,120 L55,95', main: true },
  { d: 'M155,170 L125,145 L85,145 L55,130', main: false },
  { d: 'M165,150 L140,130 L110,130 L80,105', main: false },
  // 右上
  { d: 'M240,160 L280,120 L320,120 L345,95', main: true },
  { d: 'M245,170 L275,145 L315,145 L345,130', main: false },
  { d: 'M235,150 L260,130 L290,130 L320,105', main: false },
  // 左下
  { d: 'M160,240 L120,280 L80,280 L55,305', main: true },
  { d: 'M155,230 L125,255 L85,255 L55,270', main: false },
  // 右下
  { d: 'M240,240 L280,280 L320,280 L345,305', main: true },
  { d: 'M245,230 L275,255 L315,255 L345,270', main: false },
  // 上中
  { d: 'M200,135 L200,95 L200,60', main: true },
  { d: 'M190,140 L190,110 L175,80', main: false },
  { d: 'M210,140 L210,110 L225,80', main: false },
  // 下中
  { d: 'M200,265 L200,305 L200,340', main: true },
  { d: 'M190,260 L190,290 L175,320', main: false },
]

// ── 端子位置 (电路末端小圆点) ──
const TERMINALS = [
  { x: 55, y: 95 }, { x: 55, y: 130 }, { x: 80, y: 105 },
  { x: 345, y: 95 }, { x: 345, y: 130 }, { x: 320, y: 105 },
  { x: 55, y: 305 }, { x: 55, y: 270 },
  { x: 345, y: 305 }, { x: 345, y: 270 },
  { x: 200, y: 60 }, { x: 175, y: 80 }, { x: 225, y: 80 },
  { x: 200, y: 340 }, { x: 175, y: 320 },
]

// ── 断裂弧线端子 (预计算, 避免 SSR hydration mismatch) ──
const ARC_TERMINALS = [
  { x: 350.3, y: 145.3, rot: -20 },
  { x: 227.8, y: 357.6, rot: 40 },
  { x: 172.2, y: 357.6, rot: 100 },
  { x: 49.7, y: 254.7, rot: 160 },
  { x: 77.4, y: 97.2, rot: 220 },
  { x: 222.5, y: 42.3, rot: 280 },
]

// ── 浮动碎片数据 ──
const FRAGMENTS = [
  { cx: 52, cy: 160, size: 6, shape: 'tri', rot: 15 },
  { cx: 348, cy: 155, size: 5, shape: 'diamond', rot: 30 },
  { cx: 90, cy: 50, size: 4, shape: 'hex', rot: 0 },
  { cx: 310, cy: 48, size: 5, shape: 'tri', rot: 60 },
  { cx: 45, cy: 250, size: 3, shape: 'square', rot: 45 },
  { cx: 355, cy: 260, size: 4, shape: 'diamond', rot: 10 },
  { cx: 130, cy: 345, size: 5, shape: 'hex', rot: 20 },
  { cx: 270, cy: 350, size: 4, shape: 'tri', rot: 50 },
  { cx: 65, cy: 70, size: 3, shape: 'square', rot: 25 },
  { cx: 335, cy: 335, size: 3, shape: 'diamond', rot: 70 },
]

function fragmentPath(shape: string, size: number): string {
  const s = size
  switch (shape) {
    case 'tri': return `M0,${-s} L${s * 0.87},${s * 0.5} L${-s * 0.87},${s * 0.5} Z`
    case 'diamond': return `M0,${-s} L${s},0 L0,${s} L${-s},0 Z`
    case 'hex': {
      const pts = Array.from({ length: 6 }, (_, i) => {
        const a = (Math.PI * 2 * i) / 6 - Math.PI / 2
        return `${(Math.cos(a) * s).toFixed(1)},${(Math.sin(a) * s).toFixed(1)}`
      })
      return `M${pts.join(' L')} Z`
    }
    case 'square': return `M${-s},${-s} L${s},${-s} L${s},${s} L${-s},${s} Z`
    default: return ''
  }
}

// ── 神经脉冲路径 (外层弧线) ──
const NEURAL_PATHS = [
  'M50,90 Q20,200 50,310',
  'M350,90 Q380,200 350,310',
  'M90,45 Q200,15 310,45',
  'M90,355 Q200,385 310,355',
  'M70,70 Q40,135 55,200',
  'M330,330 Q360,265 345,200',
]

interface HeroBrainLogoProps {
  className?: string
}

export function HeroBrainLogo({ className = '' }: HeroBrainLogoProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return
    if (prefersReducedMotion()) return

    const svg = svgRef.current

    // ── Timeline 编排 ──
    const tl = createTimeline({
      defaults: { ease: 'easeOutExpo' },
    })

    // t=0: Logo 缩放入场
    tl.add('.hero-logo-img', {
      scale: [0.2, 1],
      opacity: [0, 1],
      duration: 900,
    }, 0)

    // t=200: 多层环系统淡入
    tl.add('.hero-ring', {
      opacity: [0, 1],
      scale: [0.85, 1],
      duration: 700,
      delay: stagger(80),
    }, 200)

    // t=450: 刻度环旋入
    tl.add('.hero-ticks', {
      opacity: [0, 0.4],
      rotate: ['-30deg', '0deg'],
      duration: 800,
    }, 450)

    // t=550: 断裂弧线描边
    const brokenArcs = svg.querySelectorAll<SVGPathElement>('.hero-broken-arc')
    brokenArcs.forEach((path) => {
      const len = path.getTotalLength()
      path.style.strokeDasharray = `${len}`
      path.style.strokeDashoffset = `${len}`
    })
    tl.add('.hero-broken-arc', {
      strokeDashoffset: [0],
      opacity: [0, 0.7],
      duration: 1000,
      delay: stagger(120),
    }, 550)

    // t=600: 三组齿轮旋入
    tl.add('.hero-gear', {
      opacity: [0, 0.85],
      rotate: ['-120deg', '0deg'],
      scale: [0.5, 1],
      duration: 900,
      delay: stagger(150),
    }, 600)

    // t=800: 电路板线路描边
    const circuits = svg.querySelectorAll<SVGPathElement>('.hero-circuit')
    circuits.forEach((path) => {
      const len = path.getTotalLength()
      path.style.strokeDasharray = `${len}`
      path.style.strokeDashoffset = `${len}`
    })
    tl.add('.hero-circuit', {
      strokeDashoffset: [0],
      duration: 800,
      delay: stagger(60),
    }, 800)

    // t=900: 端子闪入
    tl.add('.hero-terminal', {
      opacity: [0, 0.6],
      scale: [0, 1],
      duration: 400,
      delay: stagger(30),
    }, 900)

    // t=1000: 碎片浮入
    tl.add('.hero-fragment', {
      opacity: [0, 1],
      scale: [0, 1],
      duration: 600,
      delay: stagger(60),
    }, 1000)

    // t=1100: 脉冲光点
    tl.add('.hero-pulse', {
      opacity: [0, 0.9],
      duration: 400,
      delay: stagger(80),
    }, 1100)

    // t=1200: 扫描线
    tl.add('.hero-scan-line', {
      opacity: [0, 0.15],
      duration: 600,
    }, 1200)

    // ── 永久循环动画 ──

    // 齿轮旋转
    animate('.hero-gear-left', {
      rotate: '+=360deg',
      duration: 10000,
      loop: true,
      ease: 'linear',
    })
    animate('.hero-gear-right', {
      rotate: '-=360deg',
      duration: 13000,
      loop: true,
      ease: 'linear',
    })
    animate('.hero-gear-stem', {
      rotate: '+=360deg',
      duration: 16000,
      loop: true,
      ease: 'linear',
    })

    // 环旋转
    animate('.hero-ring-rotate-cw', {
      rotate: '+=360deg',
      duration: 60000,
      loop: true,
      ease: 'linear',
    })
    animate('.hero-ring-rotate-ccw', {
      rotate: '-=360deg',
      duration: 45000,
      loop: true,
      ease: 'linear',
    })
    animate('.hero-ticks', {
      rotate: '+=360deg',
      duration: 90000,
      loop: true,
      ease: 'linear',
    })

    // 主环呼吸
    animate('.hero-ring-breathe', {
      opacity: [0.5, 0.85],
      duration: 3000,
      loop: true,
      alternate: true,
      ease: 'easeInOutSine',
    })

    // 碎片浮动
    svg.querySelectorAll<SVGElement>('.hero-fragment').forEach((frag, i) => {
      animate(frag, {
        translateY: ['-4px', '4px'],
        translateX: ['-2px', '2px'],
        rotate: `+=${i % 2 === 0 ? 15 : -15}deg`,
        opacity: [0.2 + (i % 3) * 0.1, 0.45 + (i % 3) * 0.1],
        duration: 3000 + i * 400,
        loop: true,
        alternate: true,
        ease: 'easeInOutSine',
      })
    })

    // 扫描线旋转
    animate('.hero-scan-line', {
      rotate: '+=360deg',
      duration: 8000,
      loop: true,
      ease: 'linear',
    })

    // 脉冲光点沿路径移动
    const pulses = svg.querySelectorAll<SVGCircleElement>('.hero-pulse')
    const neuralPaths = svg.querySelectorAll<SVGPathElement>('.hero-neural-path')
    pulses.forEach((pulse, i) => {
      const pathEl = neuralPaths[i % neuralPaths.length]
      if (!pathEl) return
      const len = pathEl.getTotalLength()
      animate(pulse, {
        onUpdate: (anim) => {
          const progress = (anim.currentTime % 3500) / 3500
          const point = pathEl.getPointAtLength(progress * len)
          pulse.setAttribute('cx', `${point.x}`)
          pulse.setAttribute('cy', `${point.y}`)
        },
        duration: 3500,
        loop: true,
        ease: 'linear',
        delay: i * 600,
      })
    })

    // LOGO 浮动
    animate(containerRef.current, {
      translateY: ['-6px', '6px'],
      duration: 5000,
      loop: true,
      alternate: true,
      ease: 'easeInOutSine',
    })

  }, [])

  // 齿轮 SVG 数据 (放大)
  const gearLeftPath = gearPath(100, 200, 28, 10, 7)
  const gearRightPath = gearPath(300, 200, 28, 10, 7)
  const gearStemPath = gearPath(200, 320, 22, 8, 6)

  // 刻度线
  const tickPath = tickMarks(200, 200, 172, 180, 72)

  // 断裂弧线
  const brokenArcs = brokenArc(200, 200, 160)

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* 多层发光 */}
      <div className="absolute inset-[-20%] rounded-full bg-primary/8 blur-[80px] animate-pulse-red" />
      <div className="absolute inset-[-10%] rounded-full bg-primary/5 blur-[40px]" />

      {/* SVG 动画层 */}
      <svg
        ref={svgRef}
        viewBox="0 0 400 400"
        className="absolute inset-0 w-full h-full"
        style={{ filter: 'drop-shadow(0 0 12px hsl(var(--primary) / 0.3))' }}
      >
        <defs>
          {/* 红色发光滤镜 */}
          <filter id="redGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="strongGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          {/* 渐变 */}
          <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.9" />
            <stop offset="50%" stopColor="hsl(var(--primary))" stopOpacity="0.3" />
            <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0.9" />
          </linearGradient>
          <radialGradient id="scanGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0" />
            <stop offset="70%" stopColor="hsl(var(--primary))" stopOpacity="0.05" />
            <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0.2" />
          </radialGradient>
        </defs>

        {/* ═══ 环5: 最外层极细虚线 ═══ */}
        <circle
          className="hero-ring hero-ring-rotate-ccw"
          cx="200" cy="200" r="192"
          fill="none" stroke="hsl(var(--primary))" strokeWidth="0.4"
          strokeDasharray="2 28" opacity="0"
          style={{ transformOrigin: '200px 200px' }}
        />

        {/* ═══ 环4: 刻度线环 ═══ */}
        <path
          className="hero-ticks"
          d={tickPath}
          fill="none" stroke="hsl(var(--primary))" strokeWidth="0.6"
          opacity="0"
          style={{ transformOrigin: '200px 200px' }}
        />

        {/* ═══ 环3: 断裂弧线 + 端子 ═══ */}
        {brokenArcs.map((d, i) => (
          <path
            key={`ba-${i}`}
            className="hero-ring hero-broken-arc"
            d={d}
            fill="none" stroke="url(#ringGrad)" strokeWidth="2"
            strokeLinecap="round" opacity="0"
            filter="url(#redGlow)"
          />
        ))}
        {/* 断口端子 (小方块) — 预计算坐标避免 SSR hydration mismatch */}
        {ARC_TERMINALS.map((p, i) => (
          <rect
            key={`bt-${i}`}
            className="hero-terminal"
            x={p.x - 2.5} y={p.y - 2.5} width="5" height="5"
            fill="hsl(var(--primary))" opacity="0"
            transform={`rotate(${p.rot}, ${p.x}, ${p.y})`}
            style={{ transformOrigin: `${p.x}px ${p.y}px` }}
          />
        ))}

        {/* ═══ 环2: 虚线环 ═══ */}
        <circle
          className="hero-ring hero-ring-rotate-cw hero-ring-breathe"
          cx="200" cy="200" r="145"
          fill="none" stroke="hsl(var(--primary))" strokeWidth="0.8"
          strokeDasharray="10 15" opacity="0"
          style={{ transformOrigin: '200px 200px' }}
        />

        {/* ═══ 环1: 内圈实线 + 发光 ═══ */}
        <circle
          className="hero-ring hero-ring-breathe"
          cx="200" cy="200" r="125"
          fill="none" stroke="hsl(var(--primary))" strokeWidth="1.2"
          opacity="0" filter="url(#redGlow)"
          style={{ transformOrigin: '200px 200px' }}
        />

        {/* ═══ 扫描线 ═══ */}
        <g className="hero-scan-line" style={{ transformOrigin: '200px 200px', opacity: 0 }}>
          <line x1="200" y1="200" x2="200" y2="10"
            stroke="url(#scanGrad)" strokeWidth="1.5" />
          {/* 扫描扇形 */}
          <path d="M200,200 L195,30 A170,170 0 0,1 220,32 L200,200"
            fill="hsl(var(--primary))" opacity="0.03" />
        </g>

        {/* ═══ 齿轮系统 ═══ */}
        {/* 左脑齿轮 */}
        <g className="hero-gear hero-gear-left" style={{ transformOrigin: '100px 200px', opacity: 0 }}>
          <path d={gearLeftPath} fill="none" stroke="hsl(var(--primary))" strokeWidth="1.8" filter="url(#redGlow)" />
          <circle cx="100" cy="200" r="12" fill="none" stroke="hsl(var(--primary))" strokeWidth="1" />
          <circle cx="100" cy="200" r="3" fill="hsl(var(--primary))" opacity="0.5" />
          {/* 十字准星 */}
          <line x1="94" y1="200" x2="106" y2="200" stroke="hsl(var(--primary))" strokeWidth="0.5" opacity="0.4" />
          <line x1="100" y1="194" x2="100" y2="206" stroke="hsl(var(--primary))" strokeWidth="0.5" opacity="0.4" />
          {/* 标签 */}
          <rect x="83" y="165" width="34" height="12" rx="2" fill="hsl(var(--primary))" opacity="0.12" />
          <text x="100" y="174" textAnchor="middle" fill="hsl(var(--primary))" fontSize="7" fontFamily="monospace" opacity="0.7">LEFT</text>
        </g>
        {/* 右脑齿轮 */}
        <g className="hero-gear hero-gear-right" style={{ transformOrigin: '300px 200px', opacity: 0 }}>
          <path d={gearRightPath} fill="none" stroke="hsl(var(--primary))" strokeWidth="1.8" filter="url(#redGlow)" />
          <circle cx="300" cy="200" r="12" fill="none" stroke="hsl(var(--primary))" strokeWidth="1" />
          <circle cx="300" cy="200" r="3" fill="hsl(var(--primary))" opacity="0.5" />
          <line x1="294" y1="200" x2="306" y2="200" stroke="hsl(var(--primary))" strokeWidth="0.5" opacity="0.4" />
          <line x1="300" y1="194" x2="300" y2="206" stroke="hsl(var(--primary))" strokeWidth="0.5" opacity="0.4" />
          <rect x="280" y="165" width="40" height="12" rx="2" fill="hsl(var(--primary))" opacity="0.12" />
          <text x="300" y="174" textAnchor="middle" fill="hsl(var(--primary))" fontSize="7" fontFamily="monospace" opacity="0.7">RIGHT</text>
        </g>
        {/* 脑干齿轮 */}
        <g className="hero-gear hero-gear-stem" style={{ transformOrigin: '200px 320px', opacity: 0 }}>
          <path d={gearStemPath} fill="none" stroke="hsl(var(--primary))" strokeWidth="1.8" filter="url(#redGlow)" />
          <circle cx="200" cy="320" r="10" fill="none" stroke="hsl(var(--primary))" strokeWidth="1" />
          <circle cx="200" cy="320" r="2.5" fill="hsl(var(--primary))" opacity="0.5" />
          <line x1="195" y1="320" x2="205" y2="320" stroke="hsl(var(--primary))" strokeWidth="0.5" opacity="0.4" />
          <line x1="200" y1="315" x2="200" y2="325" stroke="hsl(var(--primary))" strokeWidth="0.5" opacity="0.4" />
          <rect x="183" y="348" width="34" height="12" rx="2" fill="hsl(var(--primary))" opacity="0.12" />
          <text x="200" y="357" textAnchor="middle" fill="hsl(var(--primary))" fontSize="7" fontFamily="monospace" opacity="0.7">STEM</text>
        </g>

        {/* 齿轮连接弧线 */}
        <path className="hero-circuit" d="M128,200 Q165,200 170,195" fill="none" stroke="hsl(var(--primary))" strokeWidth="0.6" strokeDasharray="3 4" opacity="0.3" />
        <path className="hero-circuit" d="M272,200 Q235,200 230,195" fill="none" stroke="hsl(var(--primary))" strokeWidth="0.6" strokeDasharray="3 4" opacity="0.3" />
        <path className="hero-circuit" d="M200,298 Q200,275 200,265" fill="none" stroke="hsl(var(--primary))" strokeWidth="0.6" strokeDasharray="3 4" opacity="0.3" />

        {/* ═══ 电路板连线 ═══ */}
        {CIRCUIT_PATHS.map(({ d, main }, i) => (
          <path
            key={`c-${i}`}
            className="hero-circuit"
            d={d}
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth={main ? '1.5' : '0.8'}
            opacity={main ? '0.6' : '0.25'}
          />
        ))}
        {/* 端子圆点 */}
        {TERMINALS.map((t, i) => (
          <circle
            key={`t-${i}`}
            className="hero-terminal"
            cx={t.x} cy={t.y} r="2.5"
            fill="hsl(var(--primary))" opacity="0"
            style={{ transformOrigin: `${t.x}px ${t.y}px` }}
          />
        ))}

        {/* ═══ 浮动碎片 ═══ */}
        {FRAGMENTS.map((f, i) => (
          <g key={`f-${i}`} className="hero-fragment"
            style={{ transformOrigin: `${f.cx}px ${f.cy}px`, opacity: 0 }}
          >
            <path
              d={fragmentPath(f.shape, f.size)}
              fill="none" stroke="hsl(var(--primary))"
              strokeWidth="0.8" opacity="0.35"
              transform={`translate(${f.cx},${f.cy}) rotate(${f.rot})`}
            />
          </g>
        ))}

        {/* ═══ 神经脉冲路径 + 光点 ═══ */}
        {NEURAL_PATHS.map((d, i) => (
          <path key={`np-${i}`} className="hero-neural-path" d={d} fill="none" stroke="none" />
        ))}
        {NEURAL_PATHS.map((_, i) => (
          <circle
            key={`pulse-${i}`}
            className="hero-pulse"
            cx="0" cy="0" r="4.5"
            fill="hsl(var(--primary))" opacity="0"
            filter="url(#strongGlow)"
          />
        ))}
      </svg>

      {/* 层0: 中心 LOGO 图片 */}
      <div className="hero-logo-img relative z-10 w-full h-full flex items-center justify-center" style={{ opacity: 0 }}>
        <div className="relative w-[50%] h-[50%]">
          <Image
            src="/logo/logo.png"
            alt="DREAMVFIA"
            fill
            sizes="384px"
            className="object-contain"
            style={{
              filter: 'drop-shadow(0 0 25px hsl(var(--primary) / 0.5)) drop-shadow(0 0 60px hsl(var(--primary) / 0.2))',
            }}
            priority
          />
        </div>
      </div>
    </div>
  )
}
