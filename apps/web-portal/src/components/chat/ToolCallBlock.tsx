'use client'

import { useState } from 'react'
import { Wrench, Eye, ChevronDown, Globe, Clock, Calculator, FileText } from 'lucide-react'
import type { ToolStep } from '@/hooks/useStreamChat'
import { cn } from '@/lib/utils'

const TOOL_ICONS: Record<string, typeof Wrench> = {
  web_search: Globe,
  web_fetch: FileText,
  datetime: Clock,
  calculator: Calculator,
}

interface ToolCallBlockProps {
  steps: ToolStep[]
  collapsed?: boolean
}

export function ToolCallBlock({ steps, collapsed = false }: ToolCallBlockProps) {
  const [expanded, setExpanded] = useState(!collapsed)

  if (steps.length === 0) return null

  return (
    <div className="w-full mb-1.5">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-[10px] font-mono text-sky-400/70 hover:text-sky-400 transition-colors mb-1"
      >
        <Wrench size={10} />
        <span>TOOL CALLS ({steps.length})</span>
        <ChevronDown size={10} className={cn('transition-transform', expanded && 'rotate-180')} />
      </button>

      {expanded && (
        <div className="space-y-1.5">
          {steps.map((step, i) => {
            const Icon = (step.tool_name && TOOL_ICONS[step.tool_name]) || (step.type === 'tool_call' ? Wrench : Eye)
            const isCall = step.type === 'tool_call'

            return (
              <div
                key={i}
                className={cn(
                  'flex items-start gap-1.5 px-2.5 py-1.5 rounded text-[11px] font-mono border',
                  isCall
                    ? 'bg-sky-400/5 border-sky-400/20 text-sky-400/90'
                    : 'bg-emerald-400/5 border-emerald-400/20 text-emerald-400/90',
                )}
              >
                <Icon size={11} className="mt-0.5 flex-shrink-0" />
                <div className="min-w-0 flex-1">
                  {isCall ? (
                    <>
                      <span className="font-bold">
                        {step.tool_name ? step.tool_name.toUpperCase() : 'TOOL'}
                      </span>
                      {step.tool_input && (
                        <span className="text-muted-foreground/70 ml-1.5">
                          ({Object.entries(step.tool_input).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(', ')})
                        </span>
                      )}
                      {step.content && !step.tool_input && (
                        <span className="text-muted-foreground ml-1.5">— {step.content.slice(0, 100)}</span>
                      )}
                    </>
                  ) : (
                    <>
                      <span className="font-bold">RESULT</span>
                      <span className="ml-1.5 break-all">
                        {(step.tool_output || step.content || '').slice(0, 200)}
                        {(step.tool_output || step.content || '').length > 200 && '...'}
                      </span>
                    </>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
