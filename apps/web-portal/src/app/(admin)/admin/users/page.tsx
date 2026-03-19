'use client'

import Link from 'next/link'
import { useState, useEffect, useCallback } from 'react'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Plus, Copy, Check } from 'lucide-react'

interface UserItem {
  id: string
  email: string
  username: string
  displayName: string | null
  avatarUrl: string | null
  status: string
  tierLevel: number
  emailVerified: boolean
  createdAt: string
  lastLoginAt: string | null
}

interface Pagination {
  page: number
  limit: number
  total: number
  totalPages: number
}

const statusLabels: Record<string, { label: string; cls: string }> = {
  active: { label: '正常', cls: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  locked: { label: '锁定', cls: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30' },
  banned: { label: '禁用', cls: 'text-destructive bg-destructive/10 border-destructive/30' },
}

const tierLabels: Record<number, string> = {
  0: '免费',
  1: 'VIP',
  2: '企业',
  9: '管理员',
  10: '超管',
}

function CopyUID({ uid }: { uid: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={(e) => {
        e.stopPropagation()
        void navigator.clipboard.writeText(uid)
        setCopied(true)
        setTimeout(() => setCopied(false), 1500)
      }}
      className="flex items-center gap-1 text-[10px] text-muted-foreground/60 hover:text-primary transition-colors font-mono"
      title={uid}
    >
      <span>{uid.slice(0, 8)}...</span>
      {copied ? <Check size={10} className="text-emerald-400" /> : <Copy size={10} />}
    </button>
  )
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserItem[]>([])
  const [pagination, setPagination] = useState<Pagination>({ page: 1, limit: 20, total: 0, totalPages: 0 })
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState({ email: '', username: '', displayName: '', password: '', tierLevel: 0 })
  const [createError, setCreateError] = useState('')
  const [creating, setCreating] = useState(false)

  const fetchUsers = useCallback(async (page = 1) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), limit: '20' })
      if (search) params.set('search', search)
      if (statusFilter) params.set('status', statusFilter)

      const res = await fetch(`/api/admin/users?${params}`, { credentials: 'include' })
      const data = (await res.json()) as { success: boolean; users: UserItem[]; pagination: Pagination }

      if (data.success) {
        setUsers(data.users)
        setPagination(data.pagination)
      }
    } catch { /* ignore */ } finally {
      setLoading(false)
    }
  }, [search, statusFilter])

  useEffect(() => {
    void fetchUsers()
  }, [fetchUsers])

  async function handleCreateUser() {
    if (!createForm.email || !createForm.username || !createForm.password) {
      setCreateError('邮箱、用户名、密码为必填项')
      return
    }
    setCreating(true)
    setCreateError('')
    try {
      const res = await fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(createForm),
      })
      const data = (await res.json()) as { success: boolean; error?: string }
      if (data.success) {
        setShowCreate(false)
        setCreateForm({ email: '', username: '', displayName: '', password: '', tierLevel: 0 })
        void fetchUsers()
      } else {
        setCreateError(data.error || '创建失败')
      }
    } catch {
      setCreateError('网络错误')
    } finally {
      setCreating(false)
    }
  }

  async function handleAction(userId: string, action: string) {
    try {
      await fetch('/api/admin/users', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ userId, action }),
      })
      void fetchUsers(pagination.page)
    } catch { /* ignore */ }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-mono font-bold text-foreground">用户管理</h1>
          <p className="text-xs font-mono text-muted-foreground mt-1">共 {pagination.total} 位用户</p>
        </div>
        <Button size="sm" className="text-xs font-mono gap-1" onClick={() => setShowCreate(true)}>
          <Plus size={14} /> 新建用户
        </Button>
      </div>

      {/* 搜索 + 筛选 */}
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="搜索邮箱/用户名..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && void fetchUsers()}
          className="flex-1 max-w-sm bg-secondary border border-border px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 rounded-md"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-secondary border border-border px-3 py-2 text-xs font-mono text-foreground outline-none focus:border-primary/50 rounded-md"
        >
          <option value="">全部状态</option>
          <option value="active">正常</option>
          <option value="locked">锁定</option>
          <option value="banned">禁用</option>
        </select>
        <Button
          onClick={() => void fetchUsers()}
          size="sm"
          className="text-xs font-mono font-bold"
        >
          搜索
        </Button>
      </div>

      {/* 用户表格 */}
      <div className="bg-card border border-border rounded-md overflow-hidden">
        <Table className="text-xs font-mono">
          <TableHeader>
            <TableRow className="bg-secondary/50 hover:bg-secondary/50">
              <TableHead className="text-xs font-normal">用户</TableHead>
              <TableHead className="text-xs font-normal">UID</TableHead>
              <TableHead className="text-xs font-normal">邮箱</TableHead>
              <TableHead className="text-xs font-normal">状态</TableHead>
              <TableHead className="text-xs font-normal">等级</TableHead>
              <TableHead className="text-xs font-normal">注册时间</TableHead>
              <TableHead className="text-xs font-normal">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground py-8">加载中...</TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground py-8">暂无数据</TableCell>
              </TableRow>
            ) : (
              users.map((u) => {
                const st = statusLabels[u.status] ?? statusLabels.active!
                return (
                  <TableRow key={u.id}>
                    <TableCell>
                      <Link href={`/admin/users/${u.id}`} className="flex items-center gap-2 hover:text-primary transition-colors">
                        {u.avatarUrl ? (
                          /* eslint-disable-next-line @next/next/no-img-element */
                          <img src={u.avatarUrl} alt="" className="w-6 h-6 rounded-full border border-primary/20" />
                        ) : (
                          <div className="w-6 h-6 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-[10px] text-primary">
                            {(u.displayName || u.username || '?').charAt(0).toUpperCase()}
                          </div>
                        )}
                        <span className="text-foreground">{u.displayName || u.username}</span>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <CopyUID uid={u.id} />
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {u.email}
                      {!u.emailVerified && <span className="ml-1 text-yellow-500/60">(未验证)</span>}
                    </TableCell>
                    <TableCell>
                      <span className={`px-1.5 py-0.5 text-[10px] border rounded ${st.cls}`}>{st.label}</span>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {tierLabels[u.tierLevel] ?? `Lv.${u.tierLevel}`}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(u.createdAt).toLocaleDateString('zh-CN')}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {u.status === 'locked' && (
                          <Button variant="ghost" size="sm" onClick={() => void handleAction(u.id, 'activate')} className="h-6 px-2 text-[10px] text-emerald-400 hover:text-emerald-400 hover:bg-emerald-500/10">
                            解锁
                          </Button>
                        )}
                        {u.status === 'active' && (
                          <Button variant="ghost" size="sm" onClick={() => void handleAction(u.id, 'ban')} className="h-6 px-2 text-[10px] text-destructive hover:text-destructive hover:bg-destructive/10">
                            禁用
                          </Button>
                        )}
                        {u.status === 'banned' && (
                          <Button variant="ghost" size="sm" onClick={() => void handleAction(u.id, 'activate')} className="h-6 px-2 text-[10px] text-emerald-400 hover:text-emerald-400 hover:bg-emerald-500/10">
                            恢复
                          </Button>
                        )}
                        <Button variant="outline" size="sm" asChild className="h-6 px-2 text-[10px]">
                          <Link href={`/admin/users/${u.id}`}>详情</Link>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>

        {/* 分页 */}
        {pagination.totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <span className="text-[10px] text-muted-foreground">
              第 {pagination.page}/{pagination.totalPages} 页
            </span>
            <div className="flex gap-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => void fetchUsers(pagination.page - 1)}
                disabled={pagination.page <= 1}
                className="h-7 px-3 text-[10px] font-mono"
              >
                上一页
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => void fetchUsers(pagination.page + 1)}
                disabled={pagination.page >= pagination.totalPages}
                className="h-7 px-3 text-[10px] font-mono"
              >
                下一页
              </Button>
            </div>
          </div>
        )}
      </div>
      {/* 新建用户弹窗 */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-card border border-border rounded-md p-6 w-full max-w-md space-y-4">
            <h2 className="text-sm font-mono font-bold text-foreground">新建用户</h2>
            {createError && <p className="text-xs text-destructive font-mono">{createError}</p>}
            <input
              type="email"
              placeholder="邮箱 *"
              value={createForm.email}
              onChange={(e) => setCreateForm((f) => ({ ...f, email: e.target.value }))}
              className="w-full bg-secondary border border-border px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 rounded-md"
            />
            <input
              type="text"
              placeholder="用户名 *"
              value={createForm.username}
              onChange={(e) => setCreateForm((f) => ({ ...f, username: e.target.value }))}
              className="w-full bg-secondary border border-border px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 rounded-md"
            />
            <input
              type="text"
              placeholder="显示名称"
              value={createForm.displayName}
              onChange={(e) => setCreateForm((f) => ({ ...f, displayName: e.target.value }))}
              className="w-full bg-secondary border border-border px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 rounded-md"
            />
            <input
              type="password"
              placeholder="密码 *"
              value={createForm.password}
              onChange={(e) => setCreateForm((f) => ({ ...f, password: e.target.value }))}
              className="w-full bg-secondary border border-border px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 rounded-md"
            />
            <select
              value={createForm.tierLevel}
              onChange={(e) => setCreateForm((f) => ({ ...f, tierLevel: Number(e.target.value) }))}
              className="w-full bg-secondary border border-border px-3 py-2 text-xs font-mono text-foreground outline-none focus:border-primary/50 rounded-md"
            >
              <option value={0}>免费用户</option>
              <option value={1}>VIP</option>
              <option value={2}>企业</option>
              <option value={9}>管理员</option>
              <option value={10}>超管</option>
            </select>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setShowCreate(false)} className="text-xs font-mono">
                取消
              </Button>
              <Button size="sm" onClick={() => void handleCreateUser()} disabled={creating} className="text-xs font-mono">
                {creating ? '创建中...' : '创建用户'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
