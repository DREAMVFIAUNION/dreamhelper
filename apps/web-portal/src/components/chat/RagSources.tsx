'use client'

import { useState } from 'react'
import type { RagSource } from '@/hooks/useStreamChat'

interface RagSourcesProps {
  sources: RagSource[]
}

export function RagSources({ sources }: RagSourcesProps) {
  const [expanded, setExpanded] = useState(false)

  if (!sources.length) return null

  return (
    <div className="mt-2 border-t border-white/5 pt-2">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-[0.7em] text-white/40 hover:text-white/60 transition-colors"
      >
        <span className="inline-block w-3 h-3">
          <svg viewBox="0 0 16 16" fill="currentColor" className="w-3 h-3">
            <path d="M4 1.5h8a2 2 0 0 1 2 2V12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V3.5a2 2 0 0 1 2-2Zm0 1a1 1 0 0 0-1 1V12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V3.5a1 1 0 0 0-1-1H4ZM5 5h6v1H5V5Zm0 2.5h6v1H5v-1Zm0 2.5h4v1H5v-1Z" />
          </svg>
        </span>
        <span>参考来源 ({sources.length})</span>
        <span className={`transition-transform ${expanded ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {expanded && (
        <div className="mt-1.5 space-y-1.5">
          {sources.map((s, i) => (
            <div
              key={`${s.doc_id}-${i}`}
              className="px-2.5 py-1.5 bg-white/[0.02] border border-white/5 rounded text-[0.7em]"
            >
              <div className="flex items-center justify-between">
                <span className="text-white/60 font-medium">{s.title || '未知文档'}</span>
                <span className="text-white/20 text-[0.85em]">
                  相关度 {Math.round(s.score * 100)}%
                </span>
              </div>
              {s.snippet && (
                <p className="mt-0.5 text-white/30 leading-relaxed line-clamp-2">
                  {s.snippet}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
