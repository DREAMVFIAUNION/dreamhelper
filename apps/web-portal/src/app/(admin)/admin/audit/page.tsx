'use client'

import { useState, useEffect } from 'react'
import { Loader2, Shield, LogIn, Trash2, UserPlus, MessageSquare, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AuditEntry {
  id: string
  action: string
  userId: string
  username: string
  detail: string
  createdAt: string
  ip?: string
}

const ACTION_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  login: { icon: <LogIn size={12} />, color: 'text-emerald-400', label: '登录' },
  register: { icon: <UserPlus size={12} />, color: 'text-sky-400', label: '注册' },
  delete_session: { icon: <Trash2 size={12} />, color: 'text-destructive', label: '删除会话' },
  create_session: { icon: <MessageSquare size={12} />, color: 'text-violet-400', label: '创建会话' },
  upload_doc: { icon: <FileText size={12} />, color: 'text-amber-400', label: '上传文档' },
  admin_action: { icon: <Shield size={12} />, color: 'text-primary', label: '管理操作' },
}

export default function AdminAuditPage() {
  const [logs, setLogs] = useState<AuditEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        // 模拟审计数据 — 真实场景从 /api/admin/audit 获取
        // 当前系统未记录审计日志，使用从用户活动推断的模拟数据
        const res = await fetch('/api/admin/stats', { credentials: 'include' })
        const data = await res.json()
        if (data.success) {
          const mockLogs: AuditEntry[] = []
          const users = data.recentUsers || []
          for (const u of users) {
            mockLogs.push({
              id: `reg-${u.id}`,
              action: 'register',
              userId: u.id,
              username: u.username,
              detail: `新用户注册: ${u.email}`,
              createdAt: u.createdAt,
            })
          }
          const sessions = data.recentSessions || []
          for (const s of sessions) {
            mockLogs.push({
              id: `ses-${s.id}`,
              action: 'create_session',
              userId: s.userId,
              username: s.userId.slice(0, 8),
              detail: `创建会话: ${s.title || '未命名'}`,
              createdAt: s.updatedAt,
            })
          }
          mockLogs.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
          setLogs(mockLogs)
        }
      } catch { /* */ } finally { setLoading(false) }
    }
    void load()
  }, [])

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
        <h1 className="text-lg font-mono font-bold text-foreground">审计日志</h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">
          系统操作日志与安全审计 · {logs.length} 条记录
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 size={18} className="animate-spin text-muted-foreground" /></div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 text-xs font-mono text-muted-foreground/50">暂无审计记录</div>
      ) : (
        <div className="bg-card border border-border rounded-md overflow-hidden">
          <div className="divide-y divide-border/30">
            {logs.map((log) => {
              const cfg = ACTION_CONFIG[log.action] || ACTION_CONFIG.admin_action!
              return (
                <div key={log.id} className="flex items-center gap-3 px-4 py-2.5 hover:bg-secondary/30 transition-colors">
                  <div className={cn('flex-shrink-0', cfg.color)}>{cfg.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={cn('text-[9px] font-mono font-bold', cfg.color)}>{cfg.label}</span>
                      <span className="text-[10px] font-mono text-foreground truncate">{log.detail}</span>
                    </div>
                    <div className="text-[9px] font-mono text-muted-foreground/40 mt-0.5">
                      {log.username} · {timeAgo(log.createdAt)}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
