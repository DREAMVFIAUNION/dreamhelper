'use client'

import { useState, useEffect } from 'react'
import { Shield, ShieldCheck, ShieldAlert, User } from 'lucide-react'

interface StaffUser {
  id: string
  username: string
  email: string
  tierLevel: number
  status: string
  createdAt: string
}

const ROLE_MAP: Record<number, { label: string; color: string; icon: React.ReactNode }> = {
  9: { label: '超级管理员', color: 'text-primary', icon: <ShieldAlert size={12} /> },
  5: { label: '运营管理员', color: 'text-yellow-400', icon: <ShieldCheck size={12} /> },
  3: { label: '内容审核员', color: 'text-sky-400', icon: <Shield size={12} /> },
}

export default function AdminStaffPage() {
  const [staff, setStaff] = useState<StaffUser[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/admin/users', { credentials: 'include' })
        const json = await res.json()
        if (json.success && json.users) {
          const admins = json.users.filter((u: any) => u.tierLevel >= 3)
          setStaff(admins)
        }
      } catch { /* ignore */ }
      setLoading(false)
    }
    load()
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-mono font-bold text-foreground">工作人员管理</h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">管理系统管理员与工作人员权限</p>
      </div>

      {/* 角色说明 */}
      <div className="bg-card border border-border p-4 rounded-md">
        <h2 className="text-sm font-mono font-bold text-foreground mb-3">角色体系</h2>
        <div className="grid grid-cols-3 gap-3">
          {Object.entries(ROLE_MAP).map(([level, role]) => (
            <div key={level} className="px-3 py-2 bg-secondary border border-border/50 rounded-md">
              <div className={`flex items-center gap-1.5 ${role.color} mb-1`}>
                {role.icon}
                <span className="text-[10px] font-mono font-bold">{role.label}</span>
              </div>
              <div className="text-[9px] font-mono text-muted-foreground/50">tierLevel ≥ {level}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 人员列表 */}
      <div className="bg-card border border-border p-4 rounded-md">
        <h2 className="text-sm font-mono font-bold text-foreground mb-3">
          工作人员 ({staff.length})
        </h2>

        {loading ? (
          <div className="text-muted-foreground/50 text-xs font-mono animate-pulse">加载中...</div>
        ) : staff.length === 0 ? (
          <div className="text-muted-foreground/50 text-xs font-mono text-center py-6">暂无管理人员 (tierLevel ≥ 3)</div>
        ) : (
          <div className="space-y-1.5">
            {staff.map((u) => {
              const role = ROLE_MAP[u.tierLevel] || (u.tierLevel >= 9
                ? ROLE_MAP[9]
                : u.tierLevel >= 5
                  ? ROLE_MAP[5]
                  : ROLE_MAP[3])
              return (
                <div key={u.id} className="flex items-center gap-3 px-3 py-2 bg-secondary border border-border/50 text-[10px] font-mono rounded-md">
                  <User size={12} className="text-muted-foreground/60 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-foreground font-bold">{u.username}</div>
                    <div className="text-muted-foreground/50">{u.email}</div>
                  </div>
                  <div className={`flex items-center gap-1 flex-shrink-0 ${role?.color || 'text-muted-foreground'}`}>
                    {role?.icon}
                    <span>{role?.label || `Level ${u.tierLevel}`}</span>
                  </div>
                  <span className={`px-1.5 py-0.5 border text-[9px] flex-shrink-0 ${
                    u.status === 'active' ? 'text-emerald-400 border-emerald-500/30' : 'text-muted-foreground border-border'
                  }`}>
                    {u.status}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* 权限矩阵 */}
      <div className="bg-card border border-border p-4 rounded-md">
        <h2 className="text-sm font-mono font-bold text-foreground mb-3">权限矩阵</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-[9px] font-mono">
            <thead>
              <tr className="text-muted-foreground/60 border-b border-border/50">
                <th className="text-left py-1 pr-4">权限</th>
                <th className="text-center py-1 px-2">审核员(3)</th>
                <th className="text-center py-1 px-2">运营(5)</th>
                <th className="text-center py-1 px-2">超管(9)</th>
              </tr>
            </thead>
            <tbody className="text-foreground">
              {[
                ['查看仪表盘', true, true, true],
                ['查看用户列表', false, true, true],
                ['管理知识库', false, true, true],
                ['查看审计日志', false, true, true],
                ['管理组织', false, false, true],
                ['系统设置', false, false, true],
                ['管理工作人员', false, false, true],
              ].map(([perm, ...levels]) => (
                <tr key={perm as string} className="border-b border-border/20">
                  <td className="py-1 pr-4 text-muted-foreground">{perm as string}</td>
                  {(levels as boolean[]).map((v, i) => (
                    <td key={i} className="text-center py-1 px-2">
                      {v ? <span className="text-emerald-400">✓</span> : <span className="text-muted-foreground/30">—</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
