'use client'

import { useEffect, useRef, useState } from 'react'
import DOMPurify from 'dompurify'

interface MermaidRendererProps {
  chart: string
  className?: string
}

export default function MermaidRenderer({ chart, className = '' }: MermaidRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [svg, setSvg] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function render() {
      try {
        setLoading(true)
        setError('')

        // 动态加载 mermaid（避免 SSR 问题）
        const mermaid = (await import('mermaid')).default
        mermaid.initialize({
          startOnLoad: false,
          theme: 'dark',
          themeVariables: {
            darkMode: true,
            background: '#0a0e1a',
            primaryColor: '#00f0ff',
            primaryTextColor: '#e0e0ff',
            primaryBorderColor: '#00f0ff',
            lineColor: '#00f0ff',
            secondaryColor: '#1a1e3a',
            tertiaryColor: '#0d1117',
            fontFamily: 'JetBrains Mono, monospace',
          },
          flowchart: { curve: 'basis', padding: 15 },
          sequence: { actorMargin: 50, messageMargin: 40 },
        })

        const id = `mermaid-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
        const { svg: renderedSvg } = await mermaid.render(id, chart.trim())

        if (!cancelled) {
          setSvg(renderedSvg)
          setLoading(false)
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.message || 'Mermaid render failed')
          setLoading(false)
        }
      }
    }

    if (chart.trim()) {
      render()
    } else {
      setLoading(false)
    }

    return () => { cancelled = true }
  }, [chart])

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-6 rounded-lg bg-[#0a0e1a]/60 border border-cyan-500/20 ${className}`}>
        <div className="animate-pulse text-cyan-400/60 text-sm">渲染图表中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`rounded-lg bg-red-950/30 border border-red-500/30 p-4 ${className}`}>
        <div className="text-red-400 text-xs mb-2">图表渲染失败</div>
        <pre className="text-red-300/70 text-xs overflow-x-auto whitespace-pre-wrap">{error}</pre>
        <details className="mt-2">
          <summary className="text-red-400/50 text-xs cursor-pointer">查看源码</summary>
          <pre className="text-gray-400 text-xs mt-1 overflow-x-auto">{chart}</pre>
        </details>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={`mermaid-canvas rounded-lg bg-[#0a0e1a]/40 border border-cyan-500/10 p-4 overflow-x-auto ${className}`}
      dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(svg, { USE_PROFILES: { svg: true, svgFilters: true } }) }}
    />
  )
}
