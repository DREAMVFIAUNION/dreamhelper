'use client'

import { useEffect, useState } from 'react'
import { MessageSquare, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Opinion {
  topic: string
  stance: string
  confidence: number
  updated_at: number
}

export function OpinionList() {
  const [opinions, setOpinions] = useState<Opinion[]>([])
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    fetch('/api/consciousness/opinions')
      .then((r) => r.json())
      .then((data) => {
        if (data.opinions) setOpinions(data.opinions)
      })
      .catch(() => {})
  }, [])

  const display = expanded ? opinions : opinions.slice(0, 3)

  if (opinions.length === 0) {
    return (
      <div className="text-[10px] text-muted-foreground font-mono px-3 py-1">
        观点库为空 — 随对话积累
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <MessageSquare size={12} className="text-cyan-400" />
          <span className="text-xs font-mono text-muted-foreground">观点库</span>
          <span className="text-[10px] font-mono text-muted-foreground ml-1">
            {opinions.length} 条
          </span>
        </div>
        {opinions.length > 3 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-muted-foreground hover:text-primary transition-colors"
          >
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        )}
      </div>

      <div className="space-y-1.5">
        {display.map((op) => (
          <div key={op.topic} className="group">
            <div className="flex items-start gap-1.5">
              <div
                className={cn(
                  'w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1',
                  op.confidence >= 0.8
                    ? 'bg-green-400'
                    : op.confidence >= 0.5
                      ? 'bg-yellow-400'
                      : 'bg-muted-foreground',
                )}
              />
              <div className="min-w-0 flex-1">
                <span className="text-[10px] font-mono font-bold text-primary/80">
                  [{op.topic}]
                </span>
                <p className="text-[10px] font-mono text-muted-foreground leading-tight mt-0.5">
                  {op.stance}
                </p>
              </div>
              <span className="text-[9px] font-mono text-muted-foreground/50 flex-shrink-0">
                {Math.round(op.confidence * 100)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
