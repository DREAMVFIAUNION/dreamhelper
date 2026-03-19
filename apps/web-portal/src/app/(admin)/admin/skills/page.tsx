'use client'

import { useState, useEffect } from 'react'
import { Loader2, Search } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SkillItem {
  name: string
  description: string
  category: string
  args_schema: Record<string, unknown>
}

const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  daily: { label: '日常', color: 'text-emerald-400' },
  office: { label: '办公', color: 'text-sky-400' },
  coding: { label: '编程', color: 'text-violet-400' },
}

export default function AdminSkillsPage() {
  const [skills, setSkills] = useState<SkillItem[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/skills', { credentials: 'include' })
        const data = await res.json()
        if (data.skills) setSkills(data.skills)
      } catch { /* */ } finally { setLoading(false) }
    }
    void load()
  }, [])

  const filtered = skills.filter((s) => {
    if (cat && s.category !== cat) return false
    if (q && !s.name.includes(q) && !s.description.includes(q)) return false
    return true
  })

  const categories = [...new Set(skills.map((s) => s.category))]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-mono font-bold text-foreground">技能管理</h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">
          {skills.length} 个技能已注册 · {categories.length} 个分类
        </p>
      </div>

      {/* 筛选 */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1.5 bg-card border border-border px-2.5 py-1.5 flex-1 max-w-xs rounded-md">
          <Search size={13} className="text-muted-foreground" />
          <input
            type="text" value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="搜索技能..."
            className="bg-transparent text-xs font-mono text-foreground placeholder:text-muted-foreground/40 outline-none flex-1"
          />
        </div>
        <button onClick={() => setCat('')} className={cn('px-2 py-1 text-[10px] font-mono border transition-colors', !cat ? 'bg-primary/10 border-primary/30 text-primary' : 'border-border text-muted-foreground')}>
          全部
        </button>
        {categories.map((c) => (
          <button key={c} onClick={() => setCat(c)} className={cn('px-2 py-1 text-[10px] font-mono border transition-colors', cat === c ? 'bg-primary/10 border-primary/30 text-primary' : 'border-border text-muted-foreground')}>
            {CATEGORY_LABELS[c]?.label || c}
          </button>
        ))}
      </div>

      {/* 列表 */}
      {loading ? (
        <div className="flex justify-center py-12"><Loader2 size={18} className="animate-spin text-muted-foreground" /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {filtered.map((s) => {
            const catInfo = CATEGORY_LABELS[s.category]
            return (
              <div key={s.name} className="bg-card border border-border p-3 hover:border-primary/20 transition-colors rounded-md">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono font-bold text-foreground">{s.name}</span>
                  <span className={cn('text-[8px] font-mono', catInfo?.color || 'text-muted-foreground')}>
                    {catInfo?.label || s.category}
                  </span>
                </div>
                <p className="text-[10px] font-mono text-muted-foreground line-clamp-2">{s.description}</p>
                <div className="text-[8px] font-mono text-muted-foreground/40 mt-1.5">
                  {Object.keys(s.args_schema?.properties || {}).length} 个参数
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
