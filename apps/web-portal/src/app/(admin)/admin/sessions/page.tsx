'use client'

import { useState, useEffect, useCallback } from 'react'
import { Loader2, ChevronLeft, ChevronRight, Search, MessageSquare } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SessionItem {
  id: string
  title: string | null
  status: string
  createdAt: string
  updatedAt: string
  userId: string
  username: string
  email: string
  messageCount: number
}

interface Pagination {
  page: number
  limit: number
  total: number
  totalPages: number
}

export default function AdminSessionsPage() {
  const [sessions, setSessions] = useState<SessionItem[]>([])
  const [pagination, setPagination] = useState<Pagination>({ page: 1, limit: 20, total: 0, totalPages: 0 })
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const load = useCallback(async (page = 1) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), limit: '20' })
      if (q) params.set('q', q)
      if (statusFilter) params.set('status', statusFilter)
      const res = await fetch(`/api/admin/sessions?${params}`, { credentials: 'include' })
      const data = await res.json()
      if (data.success) {
        setSessions(data.sessions)
        setPagination(data.pagination)
      }
    } catch { /* */ } finally { setLoading(false) }
  }, [q, statusFilter])

  useEffect(() => { void load() }, [load])

  function timeAgo(d: string) {
    const m = Math.floor((Date.now() - new Date(d).getTime()) / 60000)
    if (m < 1) return '刚刚'
    if (m < 60) return `${m}分钟前`
    const h = Math.floor(m / 60)
    if (h < 24) return `${h}小时前`
    return `${Math.floor(h / 24)}天前`
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-mono font-bold text-foreground">对话管理</h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">
          共 {pagination.total} 个会话
        </p>
      </div>

      {/* 筛选 */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1.5 bg-card border border-border px-2.5 py-1.5 flex-1 max-w-xs rounded-md">
          <Search size={13} className="text-muted-foreground" />
          <input
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="搜索会话标题..."
            className="bg-transparent text-xs font-mono text-foreground placeholder:text-muted-foreground/40 outline-none flex-1"
          />
        </div>
        {['', 'active', 'deleted'].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={cn(
              'px-2 py-1 text-[10px] font-mono border transition-colors',
              statusFilter === s ? 'bg-primary/10 border-primary/30 text-primary' : 'border-border text-muted-foreground hover:text-foreground',
            )}
          >
            {s === '' ? '全部' : s === 'active' ? '活跃' : '已删除'}
          </button>
        ))}
      </div>

      {/* 列表 */}
      {loading ? (
        <div className="flex justify-center py-12"><Loader2 size={18} className="animate-spin text-muted-foreground" /></div>
      ) : sessions.length === 0 ? (
        <div className="text-center py-12 text-xs font-mono text-muted-foreground/50">暂无数据</div>
      ) : (
        <div className="space-y-1.5">
          {sessions.map((s) => (
            <div key={s.id} className="flex items-center gap-3 bg-card border border-border p-3 hover:border-primary/20 transition-colors rounded-md">
              <MessageSquare size={14} className="text-muted-foreground/30 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-mono font-bold text-foreground truncate">{s.title || '未命名会话'}</div>
                <div className="text-[10px] font-mono text-muted-foreground/50 mt-0.5">
                  {s.username} · {s.messageCount} 条消息 · {timeAgo(s.updatedAt)}
                </div>
              </div>
              <span className={cn(
                'text-[9px] font-mono px-1.5 py-0.5 border flex-shrink-0',
                s.status === 'active' ? 'text-emerald-400 border-emerald-500/30' : 'text-muted-foreground/40 border-border',
              )}>
                {s.status === 'active' ? '活跃' : s.status}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* 分页 */}
      {pagination.totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => void load(pagination.page - 1)}
            disabled={pagination.page <= 1}
            className="p-1 text-muted-foreground hover:text-primary disabled:opacity-30 transition-colors"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-[10px] font-mono text-muted-foreground">
            {pagination.page} / {pagination.totalPages}
          </span>
          <button
            onClick={() => void load(pagination.page + 1)}
            disabled={pagination.page >= pagination.totalPages}
            className="p-1 text-muted-foreground hover:text-primary disabled:opacity-30 transition-colors"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
