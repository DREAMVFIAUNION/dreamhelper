'use client'

import Link from 'next/link'
import { useState, useEffect, use } from 'react'
import { Copy, Check, MessageSquare, Brain, Shield, Key } from 'lucide-react'

interface UserStats { sessions: number; messages: number; memories: number }
interface UserDetail {
  id: string
  email: string
  username: string
  displayName: string | null
  avatarUrl: string | null
  status: string
  tierLevel: number
  emailVerified: boolean
  twoFactorEnabled: boolean
  createdAt: string
  updatedAt: string
  lastLoginAt: string | null
  metadata: Record<string, unknown> | null
  settings: Record<string, unknown> | null
  stats: UserStats
}

interface SessionItem { id: string; title: string | null; status: string; messageCount: number; createdAt: string; updatedAt: string }
interface MemoryItem { id: string; key: string; value: string; confidence: number; source: string | null; updatedAt: string }

type Tab = 'info' | 'sessions' | 'memories'

const statusMap: Record<string, { label: string; cls: string }> = {
  active: { label: '正常', cls: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  locked: { label: '锁定', cls: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30' },
  banned: { label: '禁用', cls: 'text-destructive bg-destructive/10 border-destructive/30' },
}

const tierLabels: Record<number, string> = { 0: '免费', 1: 'VIP', 2: '企业', 9: '管理员', 10: '超管' }

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { void navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500) }}
      className="inline-flex items-center gap-1 text-muted-foreground/60 hover:text-primary transition-colors"
      title="复制"
    >
      {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
    </button>
  )
}

export default function AdminUserDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [user, setUser] = useState<UserDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<Tab>('info')
  const [sessions, setSessions] = useState<SessionItem[]>([])
  const [memories, setMemories] = useState<MemoryItem[]>([])
  const [sessionsLoaded, setSessionsLoaded] = useState(false)
  const [memoriesLoaded, setMemoriesLoaded] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/admin/users/${id}`, { credentials: 'include' })
        const data = (await res.json()) as { success: boolean; user?: UserDetail; error?: string }
        if (data.success && data.user) {
          setUser(data.user)
        } else {
          setError(data.error || '用户不存在')
        }
      } catch {
        setError('加载失败')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [id])

  useEffect(() => {
    if (tab === 'sessions' && !sessionsLoaded) {
      void (async () => {
        try {
          const res = await fetch(`/api/admin/users/${id}/sessions`, { credentials: 'include' })
          const data = (await res.json()) as { success: boolean; sessions: SessionItem[] }
          if (data.success) setSessions(data.sessions)
        } catch { /* ignore */ }
        setSessionsLoaded(true)
      })()
    }
    if (tab === 'memories' && !memoriesLoaded) {
      void (async () => {
        try {
          const res = await fetch(`/api/admin/users/${id}/memories`, { credentials: 'include' })
          const data = (await res.json()) as { success: boolean; memories: MemoryItem[] }
          if (data.success) setMemories(data.memories)
        } catch { /* ignore */ }
        setMemoriesLoaded(true)
      })()
    }
  }, [tab, id, sessionsLoaded, memoriesLoaded])

  async function handleAction(action: string) {
    if (!user) return
    try {
      const res = await fetch(`/api/admin/users/${user.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ status: action === 'activate' ? 'active' : action === 'lock' ? 'locked' : 'banned' }),
      })
      const data = (await res.json()) as { success: boolean; user?: { status: string; tierLevel: number } }
      if (data.success && data.user) {
        setUser({ ...user, status: data.user.status, tierLevel: data.user.tierLevel })
      }
    } catch { /* ignore */ }
  }

  if (loading) return <div className="text-muted-foreground font-mono text-sm p-6">加载中...</div>

  if (error || !user) {
    return (
      <div className="p-6 space-y-4">
        <div className="text-destructive font-mono text-sm">{error || '用户不存在'}</div>
        <Link href="/admin/users" className="text-xs font-mono text-muted-foreground hover:text-primary">← 返回列表</Link>
      </div>
    )
  }

  const st = statusMap[user.status] ?? statusMap.active!

  return (
    <div className="space-y-6">
      {/* 面包屑 */}
      <div className="flex items-center gap-2 text-[10px] font-mono text-muted-foreground">
        <Link href="/admin/users" className="hover:text-primary transition-colors">用户管理</Link>
        <span>/</span>
        <span className="text-foreground">{user.displayName || user.username}</span>
      </div>

      {/* 用户信息卡 */}
      <div className="bg-card border border-border rounded-md p-6">
        <div className="flex items-start gap-4">
          {user.avatarUrl ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img src={user.avatarUrl} alt="" className="w-16 h-16 rounded-full border-2 border-primary/30" />
          ) : (
            <div className="w-16 h-16 rounded-full bg-primary/20 border-2 border-primary/40 flex items-center justify-center text-xl font-mono text-primary">
              {(user.displayName || user.username || '?').charAt(0).toUpperCase()}
            </div>
          )}
          <div className="flex-1">
            <h1 className="text-lg font-mono font-bold text-foreground">{user.displayName || user.username}</h1>
            <p className="text-xs font-mono text-muted-foreground mt-0.5">@{user.username}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className={`px-2 py-0.5 text-[10px] font-mono border ${st.cls}`}>{st.label}</span>
              {!user.emailVerified && (
                <span className="px-2 py-0.5 text-[10px] font-mono text-yellow-500 bg-yellow-500/10 border border-yellow-500/30">邮箱未验证</span>
              )}
            </div>
          </div>
          {/* 统计卡片 */}
          <div className="hidden sm:flex gap-4">
            <div className="text-center">
              <div className="text-lg font-mono font-bold text-primary">{user.stats.sessions}</div>
              <div className="text-[10px] text-muted-foreground">会话</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-mono font-bold text-primary">{user.stats.messages}</div>
              <div className="text-[10px] text-muted-foreground">消息</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-mono font-bold text-primary">{user.stats.memories}</div>
              <div className="text-[10px] text-muted-foreground">记忆</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-6 text-xs font-mono">
          <div>
            <div className="text-muted-foreground mb-0.5">邮箱</div>
            <div className="text-foreground">{user.email}</div>
          </div>
          <div>
            <div className="text-muted-foreground mb-0.5">等级</div>
            <div className="text-foreground">
              {tierLabels[user.tierLevel] ?? `Lv.${user.tierLevel}`}
              {user.tierLevel >= 9 && <span className="text-primary ml-1">(管理员)</span>}
            </div>
          </div>
          <div>
            <div className="text-muted-foreground mb-0.5 flex items-center gap-1">UID <CopyButton text={user.id} /></div>
            <div className="text-foreground truncate text-[10px]" title={user.id}>{user.id}</div>
          </div>
          <div>
            <div className="text-muted-foreground mb-0.5">注册时间</div>
            <div className="text-foreground">{new Date(user.createdAt).toLocaleString('zh-CN')}</div>
          </div>
          <div>
            <div className="text-muted-foreground mb-0.5">最后登录</div>
            <div className="text-foreground">{user.lastLoginAt ? new Date(user.lastLoginAt).toLocaleString('zh-CN') : '—'}</div>
          </div>
          <div>
            <div className="text-muted-foreground mb-0.5">安全</div>
            <div className="flex items-center gap-2 text-foreground">
              {user.twoFactorEnabled ? <Shield size={12} className="text-emerald-400" /> : <Key size={12} className="text-muted-foreground/40" />}
              {user.twoFactorEnabled ? '2FA 已启用' : '基础认证'}
            </div>
          </div>
        </div>
      </div>

      {/* Tab 切换 */}
      <div className="flex gap-1 border-b border-border">
        {([
          { key: 'info' as Tab, label: '管理操作', icon: Shield },
          { key: 'sessions' as Tab, label: `聊天记录 (${user.stats.sessions})`, icon: MessageSquare },
          { key: 'memories' as Tab, label: `用户画像 (${user.stats.memories})`, icon: Brain },
        ]).map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-mono border-b-2 transition-colors ${
              tab === key ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Icon size={12} /> {label}
          </button>
        ))}
      </div>

      {/* Tab 内容 */}
      {tab === 'info' && (
        <div className="bg-card border border-border rounded-md p-5">
          <h2 className="text-sm font-mono font-bold text-foreground mb-4">管理操作</h2>
          <div className="flex flex-wrap gap-2">
            {user.status === 'active' && (
              <>
                <button onClick={() => void handleAction('lock')} className="px-4 py-2 text-xs font-mono text-yellow-500 border border-yellow-500/30 hover:bg-yellow-500/10 transition-colors rounded-md">
                  锁定账号
                </button>
                <button onClick={() => void handleAction('ban')} className="px-4 py-2 text-xs font-mono text-destructive border border-destructive/30 hover:bg-destructive/10 transition-colors rounded-md">
                  禁用账号
                </button>
              </>
            )}
            {user.status === 'locked' && (
              <button onClick={() => void handleAction('activate')} className="px-4 py-2 text-xs font-mono text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/10 transition-colors rounded-md">
                解锁账号
              </button>
            )}
            {user.status === 'banned' && (
              <button onClick={() => void handleAction('activate')} className="px-4 py-2 text-xs font-mono text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/10 transition-colors rounded-md">
                恢复账号
              </button>
            )}
          </div>
        </div>
      )}

      {tab === 'sessions' && (
        <div className="bg-card border border-border rounded-md overflow-hidden">
          {!sessionsLoaded ? (
            <div className="text-center text-muted-foreground text-xs font-mono py-8">加载中...</div>
          ) : sessions.length === 0 ? (
            <div className="text-center text-muted-foreground text-xs font-mono py-8">暂无聊天记录</div>
          ) : (
            <div className="divide-y divide-border">
              {sessions.map((s) => (
                <div key={s.id} className="px-4 py-3 flex items-center justify-between hover:bg-secondary/30 transition-colors">
                  <div>
                    <div className="text-xs font-mono text-foreground">{s.title || '未命名对话'}</div>
                    <div className="text-[10px] font-mono text-muted-foreground mt-0.5">
                      {s.messageCount} 条消息 · {new Date(s.updatedAt).toLocaleString('zh-CN')}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] font-mono text-muted-foreground">
                    <CopyButton text={s.id} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'memories' && (
        <div className="bg-card border border-border rounded-md overflow-hidden">
          {!memoriesLoaded ? (
            <div className="text-center text-muted-foreground text-xs font-mono py-8">加载中...</div>
          ) : memories.length === 0 ? (
            <div className="text-center text-muted-foreground text-xs font-mono py-8">暂无用户画像数据</div>
          ) : (
            <div className="divide-y divide-border">
              {memories.map((m) => (
                <div key={m.id} className="px-4 py-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-primary">{m.key}</span>
                    <span className="text-[10px] font-mono text-muted-foreground">
                      置信度 {(m.confidence * 100).toFixed(0)}% · {new Date(m.updatedAt).toLocaleString('zh-CN')}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-foreground mt-1">{m.value}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
