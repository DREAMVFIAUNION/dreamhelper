'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Loader2 } from 'lucide-react'
import { PsdIcon } from '@/components/ui/PsdIcon'

interface AdminStats {
  totalUsers: number
  activeUsers: number
  totalSessions: number
  activeSessions: number
  totalMessages: number
  totalAgents: number
  totalKnowledgeBases: number
  todayUsers: number
  todayMessages: number
}

interface RecentUser {
  id: string
  username: string
  email: string
  createdAt: string
  status: string
}

interface RecentSession {
  id: string
  title: string | null
  updatedAt: string
  userId: string
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [recentUsers, setRecentUsers] = useState<RecentUser[]>([])
  const [recentSessions, setRecentSessions] = useState<RecentSession[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await fetch('/api/admin/stats', { credentials: 'include' })
        const data = await res.json()
        if (data.success) {
          setStats(data.stats)
          setRecentUsers(data.recentUsers || [])
          setRecentSessions(data.recentSessions || [])
        }
      } catch {
        console.error('[admin] stats fetch failed')
      } finally {
        setLoading(false)
      }
    }
    void fetchStats()
  }, [])

  const cards = [
    { label: '注册用户', value: stats?.totalUsers, sub: `活跃 ${stats?.activeUsers ?? 0}`, iconName: 'friends', iconSet: 'psd-simple' as const, href: '/admin/users' },
    { label: '活跃会话', value: stats?.activeSessions, sub: `总计 ${stats?.totalSessions ?? 0}`, iconName: 'comments', iconSet: 'psd-simple' as const, href: '/admin/sessions' },
    { label: '总消息数', value: stats?.totalMessages, sub: `今日 ${stats?.todayMessages ?? 0}`, iconName: 'graph_chart', iconSet: 'psd-brankic' as const, href: '/admin/analytics' },
    { label: '智能体', value: stats?.totalAgents, sub: '', iconName: 'marvin', iconSet: 'psd-brankic' as const, href: '/admin/agents' },
    { label: '知识库', value: stats?.totalKnowledgeBases, sub: '', iconName: 'encyclopedia', iconSet: 'psd-classic' as const, href: '/admin/knowledge' },
    { label: '今日新用户', value: stats?.todayUsers, sub: '', iconName: 'follow', iconSet: 'psd-simple' as const, href: '/admin/users' },
  ]

  function timeAgo(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime()
    const m = Math.floor(diff / 60000)
    if (m < 1) return '刚刚'
    if (m < 60) return `${m}分钟前`
    const h = Math.floor(m / 60)
    if (h < 24) return `${h}小时前`
    return `${Math.floor(h / 24)}天前`
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-mono font-bold text-foreground">管理面板</h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">系统运行状态总览</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => (
          <Link
            key={card.label}
            href={card.href}
            className="bg-card border border-border p-4 hover:border-primary/40 transition-all rounded-md group"
          >
            <div className="flex items-center justify-between">
              <PsdIcon name={card.iconName} set={card.iconSet} size={24} />
              <span className="text-[10px] font-mono text-muted-foreground/50 group-hover:text-primary transition-colors">
                查看详情 →
              </span>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-mono font-bold text-foreground">
                {loading ? <Loader2 size={18} className="animate-spin text-muted-foreground" /> : (card.value ?? 0)}
              </div>
              <div className="text-xs font-mono text-muted-foreground mt-0.5">{card.label}</div>
              {card.sub && (
                <div className="text-[10px] font-mono text-muted-foreground/50 mt-0.5">{card.sub}</div>
              )}
            </div>
          </Link>
        ))}
      </div>

      {/* 快捷操作 */}
      <div className="bg-card border border-border p-4 rounded-md">
        <h2 className="text-sm font-mono font-bold text-foreground mb-3">快捷操作</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <Link href="/admin/users" className="px-3 py-2 bg-secondary border border-border text-xs font-mono text-muted-foreground hover:text-primary hover:border-primary/40 text-center transition-all rounded-md">
            用户管理
          </Link>
          <Link href="/admin/agents" className="px-3 py-2 bg-secondary border border-border text-xs font-mono text-muted-foreground hover:text-primary hover:border-primary/40 text-center transition-all rounded-md">
            智能体管理
          </Link>
          <Link href="/admin/audit" className="px-3 py-2 bg-secondary border border-border text-xs font-mono text-muted-foreground hover:text-primary hover:border-primary/40 text-center transition-all rounded-md">
            审计日志
          </Link>
          <Link href="/admin/system" className="px-3 py-2 bg-secondary border border-border text-xs font-mono text-muted-foreground hover:text-primary hover:border-primary/40 text-center transition-all rounded-md">
            系统设置
          </Link>
        </div>
      </div>

      {/* 最近活动 — 双列 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 最近注册 */}
        <div className="bg-card border border-border p-4 rounded-md">
          <h2 className="text-sm font-mono font-bold text-foreground mb-3">最近注册用户</h2>
          {loading ? (
            <div className="flex justify-center py-6"><Loader2 size={16} className="animate-spin text-muted-foreground" /></div>
          ) : recentUsers.length === 0 ? (
            <div className="text-xs font-mono text-muted-foreground/50 text-center py-6">暂无数据</div>
          ) : (
            <div className="space-y-2">
              {recentUsers.map((u) => (
                <div key={u.id} className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className={`w-1.5 h-1.5 rounded-full ${u.status === 'active' ? 'bg-emerald-400' : 'bg-muted-foreground/30'}`} />
                    <span className="text-foreground truncate">{u.username}</span>
                    <span className="text-muted-foreground/50 truncate">{u.email}</span>
                  </div>
                  <span className="text-muted-foreground/40 flex-shrink-0 ml-2">{timeAgo(u.createdAt)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 最近会话 */}
        <div className="bg-card border border-border p-4 rounded-md">
          <h2 className="text-sm font-mono font-bold text-foreground mb-3">最近活跃会话</h2>
          {loading ? (
            <div className="flex justify-center py-6"><Loader2 size={16} className="animate-spin text-muted-foreground" /></div>
          ) : recentSessions.length === 0 ? (
            <div className="text-xs font-mono text-muted-foreground/50 text-center py-6">暂无数据</div>
          ) : (
            <div className="space-y-2">
              {recentSessions.map((s) => (
                <div key={s.id} className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2 min-w-0">
                    <PsdIcon name="comments" set="psd-simple" size={12} />
                    <span className="text-foreground truncate">{s.title || '未命名会话'}</span>
                  </div>
                  <span className="text-muted-foreground/40 flex-shrink-0 ml-2">{timeAgo(s.updatedAt)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
