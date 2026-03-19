'use client'

import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AnalyticsData {
  days: number
  series: { labels: string[]; users: number[]; sessions: number[]; messages: number[] }
  totals: { users: number; sessions: number; messages: number }
}

function MiniChart({ data, color, height = 80 }: { data: number[]; color: string; height?: number }) {
  if (!data.length) return null
  const max = Math.max(...data, 1)
  const w = 100
  const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${height - (v / max) * (height - 8)}`).join(' ')
  const areaPoints = `0,${height} ${points} ${w},${height}`

  return (
    <svg viewBox={`0 0 ${w} ${height}`} className="w-full" preserveAspectRatio="none" style={{ height }}>
      <polygon points={areaPoints} fill={`${color}15`} />
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
      {data.length > 0 && (
        <circle
          cx={(data.length - 1) / (data.length - 1) * w}
          cy={height - (data[data.length - 1]! / max) * (height - 8)}
          r="2.5" fill={color}
        />
      )}
    </svg>
  )
}

export default function AdminAnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(14)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const res = await fetch(`/api/admin/analytics?days=${days}`, { credentials: 'include' })
        const d = await res.json()
        if (d.success) setData(d)
      } catch { /* */ } finally { setLoading(false) }
    }
    void load()
  }, [days])

  const charts = data ? [
    { label: '新增用户', total: data.totals.users, data: data.series.users, color: '#FE0000', unit: '人' },
    { label: '新增会话', total: data.totals.sessions, data: data.series.sessions, color: '#4ECDC4', unit: '个' },
    { label: '消息数', total: data.totals.messages, data: data.series.messages, color: '#FFB800', unit: '条' },
  ] : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-mono font-bold text-foreground">数据分析</h1>
          <p className="text-xs font-mono text-muted-foreground mt-1">最近 {days} 天趋势</p>
        </div>
        <div className="flex gap-1">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={cn(
                'px-2 py-0.5 text-[10px] font-mono border transition-colors',
                days === d ? 'bg-primary/10 border-primary/30 text-primary' : 'border-border text-muted-foreground',
              )}
            >
              {d}天
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 size={18} className="animate-spin text-muted-foreground" /></div>
      ) : (
        <>
          {/* 趋势图卡片 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {charts.map((c) => (
              <div key={c.label} className="bg-card border border-border p-4 rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono text-muted-foreground">{c.label}</span>
                  <span className="text-xs font-mono font-bold text-foreground">{c.total} {c.unit}</span>
                </div>
                <MiniChart data={c.data} color={c.color} />
                <div className="flex justify-between mt-1.5 text-[8px] font-mono text-muted-foreground/40">
                  <span>{data?.series.labels[0]?.slice(5)}</span>
                  <span>{data?.series.labels[data.series.labels.length - 1]?.slice(5)}</span>
                </div>
              </div>
            ))}
          </div>

          {/* 每日明细表 */}
          {data && (
            <div className="bg-card border border-border rounded-md overflow-hidden">
              <div className="px-4 py-2 border-b border-border">
                <span className="text-xs font-mono font-bold text-foreground">每日明细</span>
              </div>
              <div className="overflow-x-auto max-h-64 scrollbar-none">
                <table className="w-full text-[10px] font-mono">
                  <thead>
                    <tr className="border-b border-border text-muted-foreground">
                      <th className="text-left px-4 py-1.5">日期</th>
                      <th className="text-right px-4 py-1.5">用户</th>
                      <th className="text-right px-4 py-1.5">会话</th>
                      <th className="text-right px-4 py-1.5">消息</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.series.labels.slice().reverse().map((label, ri) => {
                      const i = data.series.labels.length - 1 - ri
                      return (
                        <tr key={label} className="border-b border-border/30 hover:bg-secondary/30">
                          <td className="px-4 py-1 text-foreground">{label}</td>
                          <td className="px-4 py-1 text-right text-muted-foreground">{data.series.users[i]}</td>
                          <td className="px-4 py-1 text-right text-muted-foreground">{data.series.sessions[i]}</td>
                          <td className="px-4 py-1 text-right text-muted-foreground">{data.series.messages[i]}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
