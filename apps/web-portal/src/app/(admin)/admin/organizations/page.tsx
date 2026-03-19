'use client'

import { useState, useEffect } from 'react'
import { Building2, Users, Crown, Calendar } from 'lucide-react'

interface OrgItem {
  id: string
  name: string
  slug: string
  memberCount: number
  createdAt: string
  owner?: { username: string }
}

export default function AdminOrganizationsPage() {
  const [orgs, setOrgs] = useState<OrgItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/admin/stats', { credentials: 'include' })
        const json = await res.json()
        // Org data may not be fully implemented in API yet, use mock fallback
        if (json.success) {
          setOrgs([
            { id: '1', name: 'DREAMVFIA UNION', slug: 'dreamvfia', memberCount: json.totalUsers || 1, createdAt: '2026-02-17T00:00:00Z', owner: { username: 'admin' } },
          ])
        }
      } catch { /* ignore */ }
      setLoading(false)
    }
    load()
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-mono font-bold text-foreground">组织管理</h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">管理企业组织与团队</p>
      </div>

      {/* 统计 */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: '组织总数', value: orgs.length, icon: <Building2 size={14} />, color: 'text-sky-400' },
          { label: '总成员', value: orgs.reduce((s, o) => s + o.memberCount, 0), icon: <Users size={14} />, color: 'text-emerald-400' },
          { label: '计费方案', value: '企业版', icon: <Crown size={14} />, color: 'text-primary' },
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

      {/* 组织列表 */}
      <div className="bg-card border border-border p-4 rounded-md">
        <h2 className="text-sm font-mono font-bold text-foreground mb-3">组织列表</h2>
        {loading ? (
          <div className="text-muted-foreground/50 text-xs font-mono animate-pulse">加载中...</div>
        ) : (
          <div className="space-y-2">
            {orgs.map((org) => (
              <div key={org.id} className="flex items-center gap-3 px-4 py-3 bg-secondary border border-border/50 rounded-md">
                <Building2 size={16} className="text-sky-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-mono font-bold text-foreground">{org.name}</div>
                  <div className="text-[9px] font-mono text-muted-foreground/50">slug: {org.slug} · 创建者: {org.owner?.username || '—'}</div>
                </div>
                <div className="flex items-center gap-1 text-[10px] font-mono text-muted-foreground/60 flex-shrink-0">
                  <Users size={10} />
                  <span>{org.memberCount}</span>
                </div>
                <div className="flex items-center gap-1 text-[10px] font-mono text-muted-foreground/40 flex-shrink-0">
                  <Calendar size={10} />
                  <span>{new Date(org.createdAt).toLocaleDateString('zh-CN')}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 配额说明 */}
      <div className="bg-card border border-border p-4 rounded-md">
        <h2 className="text-sm font-mono font-bold text-foreground mb-3">配额与计费</h2>
        <div className="grid grid-cols-2 gap-3 text-[10px] font-mono">
          {[
            { label: 'API 调用', value: '不限', used: '—' },
            { label: '知识库', value: '10 个/组织', used: '1 已用' },
            { label: '成员上限', value: '50 人', used: `${orgs[0]?.memberCount || 0} 已用` },
            { label: '存储空间', value: '10 GB', used: '< 1 MB' },
          ].map((q) => (
            <div key={q.label} className="px-3 py-2 bg-secondary border border-border/30 rounded-md">
              <div className="text-muted-foreground/60">{q.label}</div>
              <div className="text-foreground font-bold">{q.value}</div>
              <div className="text-muted-foreground/40">{q.used}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
