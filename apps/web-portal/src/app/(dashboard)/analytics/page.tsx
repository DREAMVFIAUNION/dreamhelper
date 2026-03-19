'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { BarChart3, MessageSquare, MessagesSquare, Calendar } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface AnalyticsData {
  days: number
  series: { labels: string[]; sessions: number[]; messages: number[]; userMessages: number[] }
  totals: { sessions: number; messages: number; periodSessions: number; periodMessages: number }
}

function MiniChart({ data, color }: { data: number[]; color: string }) {
  if (!data.length) return null
  const max = Math.max(...data, 1)
  const w = 240
  const h = 60
  const points = data.map((v, i) => `${(i / Math.max(data.length - 1, 1)) * w},${h - (v / max) * h}`)
  const areaPoints = `0,${h} ${points.join(' ')} ${w},${h}`
  return (
    <svg width={w} height={h} className="opacity-80">
      <polygon points={areaPoints} fill={color} fillOpacity="0.15" />
      <polyline points={points.join(' ')} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  )
}

export default function AnalyticsPage() {
  const t = useTranslations('analytics')
  const tc = useTranslations('common')
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [days, setDays] = useState(14)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/dashboard/analytics?days=${days}`, { credentials: 'include' })
      const json = await res.json()
      if (json.success) setData(json)
    } catch { /* ignore */ }
    setLoading(false)
  }, [days])

  useEffect(() => { fetchData() }, [fetchData])

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-1 h-8 bg-primary rounded-full shadow-[0_0_8px_hsl(var(--primary)/0.4)]" />
          <div>
            <h1 className="font-display text-xl font-bold text-foreground tracking-wider">{t('title')}</h1>
            <p className="text-xs font-mono text-muted-foreground mt-0.5">{t('subtitle')}</p>
          </div>
        </div>
        <div className="flex gap-1">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={cn(
                'px-2.5 py-1 text-[10px] font-mono border rounded-md transition-all',
                days === d ? 'bg-primary/10 border-primary/40 text-primary' : 'border-border text-muted-foreground hover:text-foreground'
              )}
            >
              {t('days', { d })}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-muted-foreground font-mono text-sm animate-pulse">{tc('loading')}</div>
      ) : !data ? (
        <div className="text-muted-foreground font-mono text-sm">{tc('noData')}</div>
      ) : (
        <div className="space-y-6">
          {/* 总计卡片 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: t('totalSessions'), value: data.totals.sessions, icon: <Calendar size={14} />, color: 'text-cyan-400' },
              { label: t('totalMessages'), value: data.totals.messages, icon: <MessagesSquare size={14} />, color: 'text-emerald-400' },
              { label: t('periodSessions', { d: days }), value: data.totals.periodSessions, icon: <BarChart3 size={14} />, color: 'text-primary' },
              { label: t('periodMessages', { d: days }), value: data.totals.periodMessages, icon: <MessageSquare size={14} />, color: 'text-yellow-500' },
            ].map((c) => (
              <Card key={c.label}>
                <CardContent className="p-3">
                  <div className="flex items-center gap-1.5 text-muted-foreground/60 mb-1">
                    {c.icon}
                    <span className="text-[9px] font-mono">{c.label}</span>
                  </div>
                  <div className={`text-xl font-mono font-bold ${c.color}`}>{c.value}</div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* 图表 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-mono">{t('messageTrend')}</CardTitle>
              </CardHeader>
              <CardContent>
                <MiniChart data={data.series.messages} color="#00E5FF" />
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-mono">{t('sessionTrend')}</CardTitle>
              </CardHeader>
              <CardContent>
                <MiniChart data={data.series.sessions} color="#FE0000" />
              </CardContent>
            </Card>
          </div>

          {/* 每日明细 */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-mono">{t('dailyDetail')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-[10px] font-mono">
                  <thead>
                    <tr className="text-muted-foreground/60 border-b border-border/50">
                      <th className="text-left py-1 pr-4">{t('date')}</th>
                      <th className="text-right py-1 px-2">{t('sessions')}</th>
                      <th className="text-right py-1 px-2">{t('messages')}</th>
                      <th className="text-right py-1 px-2">{t('myMessages')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.series.labels.slice().reverse().slice(0, 14).map((date, i) => {
                      const ri = data.series.labels.length - 1 - i
                      return (
                        <tr key={date} className="border-b border-border/20 text-foreground">
                          <td className="py-1 pr-4 text-muted-foreground">{date}</td>
                          <td className="text-right py-1 px-2">{data.series.sessions[ri]}</td>
                          <td className="text-right py-1 px-2">{data.series.messages[ri]}</td>
                          <td className="text-right py-1 px-2">{data.series.userMessages[ri]}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
