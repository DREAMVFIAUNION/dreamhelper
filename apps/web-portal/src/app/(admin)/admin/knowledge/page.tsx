'use client'

import { useState, useEffect } from 'react'
import { BookOpen, FileText, Database, RefreshCw } from 'lucide-react'

interface KBItem {
  id: string
  name: string
  description: string
  ownerId: string
  ownerName?: string
  docCount: number
  createdAt: string
}

export default function AdminKnowledgePage() {
  const [kbs, setKbs] = useState<KBItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/knowledge', { credentials: 'include' })
        const json = await res.json()
        if (json.success && json.knowledgeBases) {
          setKbs(json.knowledgeBases.map((kb: any) => ({
            id: kb.id,
            name: kb.name,
            description: kb.description || '',
            ownerId: kb.ownerId || '',
            docCount: kb._count?.documents ?? kb.docCount ?? 0,
            createdAt: kb.createdAt,
          })))
        }
      } catch { /* ignore */ }
      setLoading(false)
    }
    load()
  }, [])

  const totalDocs = kbs.reduce((s, k) => s + k.docCount, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-mono font-bold text-foreground">知识库管理</h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">管理系统知识库与文档</p>
      </div>

      {/* 统计 */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: '知识库', value: kbs.length, icon: <Database size={14} />, color: 'text-sky-400' },
          { label: '文档总数', value: totalDocs, icon: <FileText size={14} />, color: 'text-emerald-400' },
          { label: 'RAG 状态', value: '在线', icon: <BookOpen size={14} />, color: 'text-primary' },
        ].map((c) => (
          <div key={c.label} className="bg-card border border-border p-3 rounded-md">
            <div className="flex items-center gap-1.5 text-muted-foreground/60 mb-1">
              {c.icon}
              <span className="text-[9px] font-mono">{c.label}</span>
            </div>
            <div className={`text-lg font-mono font-bold ${c.color}`}>{c.value}</div>
          </div>
        ))}
      </div>

      {/* 列表 */}
      <div className="bg-card border border-border p-4 rounded-md">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-mono font-bold text-foreground">知识库列表</h2>
          <button onClick={() => window.location.reload()} className="text-muted-foreground hover:text-primary transition-colors">
            <RefreshCw size={12} />
          </button>
        </div>

        {loading ? (
          <div className="text-muted-foreground/50 text-xs font-mono animate-pulse">加载中...</div>
        ) : kbs.length === 0 ? (
          <div className="text-muted-foreground/50 text-xs font-mono text-center py-6">暂无知识库</div>
        ) : (
          <div className="space-y-1.5">
            {kbs.map((kb) => (
              <div key={kb.id} className="flex items-center gap-3 px-3 py-2 bg-secondary border border-border/50 text-[10px] font-mono rounded-md">
                <BookOpen size={12} className="text-sky-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-foreground font-bold truncate">{kb.name}</div>
                  <div className="text-muted-foreground/50">{kb.description || '无描述'}</div>
                </div>
                <div className="text-muted-foreground/60 flex-shrink-0">{kb.docCount} 文档</div>
                <div className="text-muted-foreground/40 flex-shrink-0 w-20 text-right">
                  {new Date(kb.createdAt).toLocaleDateString('zh-CN')}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
