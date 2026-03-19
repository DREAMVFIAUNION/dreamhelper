'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { MessageSquare, Zap, BookOpen, Clock, ArrowRight, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

interface DashboardStats {
  totalSessions: number
  todaySessions: number
  totalMessages: number
  todayMessages: number
  totalDocs: number
}

interface RecentSession {
  id: string
  title: string | null
  updatedAt: string
  messageCount: number
}

export default function DashboardPage() {
  const t = useTranslations('dashboard')
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recent, setRecent] = useState<RecentSession[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/dashboard/stats', { credentials: 'include' })
        const data = await res.json()
        if (data.success) {
          setStats(data.stats)
          setRecent(data.recentSessions || [])
        }
      } catch {
        console.error('[dashboard] stats fetch failed')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  function timeAgo(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime()
    const m = Math.floor(diff / 60000)
    if (m < 1) return t('justNow')
    if (m < 60) return t('minutesAgo', { m })
    const h = Math.floor(m / 60)
    if (h < 24) return t('hoursAgo', { h })
    return t('daysAgo', { d: Math.floor(h / 24) })
  }

  const statCards = [
    { title: t('todaySessions'), value: stats?.todaySessions ?? 0, sub: `${t('totalPrefix')} ${stats?.totalSessions ?? 0}`, unit: t('unitSessions'), icon: MessageSquare, color: 'text-primary', href: '/chat' },
    { title: t('todayMessages'), value: stats?.todayMessages ?? 0, sub: `${t('totalPrefix')} ${stats?.totalMessages ?? 0}`, unit: t('unitMessages'), icon: Zap, color: 'text-amber-400', href: '/chat' },
    { title: t('knowledgeBase'), value: stats?.totalDocs ?? 0, sub: t('uploadDocs'), unit: t('unitDocs'), icon: BookOpen, color: 'text-cyan-400', href: '/knowledge' },
  ]

  const quickActions = [
    { href: '/chat', icon: MessageSquare, title: t('startChat'), desc: t('startChatDesc'), color: 'text-primary' },
    { href: '/knowledge', icon: BookOpen, title: t('knowledgeBase'), desc: t('knowledgeDesc'), color: 'text-cyan-400' },
    { href: '/settings', icon: Zap, title: t('personalSettings'), desc: t('personalSettingsDesc'), color: 'text-amber-400' },
  ]

  return (
    <div className="p-3 sm:p-6 space-y-6 max-w-6xl">
      {/* 页面标题 */}
      <div className="flex items-center gap-3">
        <div className="w-1 h-8 bg-primary rounded-full shadow-[0_0_8px_hsl(var(--primary)/0.4)]" />
        <div>
          <h1 className="font-display text-xl font-bold text-foreground tracking-wider">{t('title')}</h1>
          <p className="text-xs font-mono text-muted-foreground mt-0.5">{t('subtitle')}</p>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((card) => (
          <Link key={card.title} href={card.href}>
            <Card className="hover:border-primary/30 hover:shadow-[0_0_15px_hsl(var(--primary)/0.08)] transition-all group cursor-pointer">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardDescription className="text-xs font-mono tracking-widest uppercase">
                    {card.title}
                  </CardDescription>
                  <card.icon size={16} className={cn(card.color, 'opacity-60 group-hover:opacity-100 transition-opacity')} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-end gap-2">
                  {loading ? (
                    <div className="h-9 w-16 animate-pulse rounded bg-muted" />
                  ) : (
                    <span className="font-display text-3xl font-black text-foreground">{card.value}</span>
                  )}
                  <span className="text-sm font-mono text-muted-foreground mb-1">{card.unit}</span>
                </div>
                <p className="text-[10px] font-mono text-muted-foreground/50 mt-1">{card.sub}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* 快捷操作 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {quickActions.map((action) => (
          <Link key={action.href} href={action.href}>
            <Card className="hover:border-primary/30 transition-all group cursor-pointer">
              <CardContent className="flex items-center gap-3 p-4">
                <action.icon size={18} className={action.color} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-mono font-bold text-foreground">{action.title}</p>
                  <p className="text-[10px] font-mono text-muted-foreground">{action.desc}</p>
                </div>
                <ArrowRight size={14} className="text-muted-foreground/30 group-hover:text-primary transition-colors shrink-0" />
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* 最近对话 */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-mono">{t('recentChats')}</CardTitle>
            <Button variant="link" size="sm" asChild className="text-[10px] font-mono h-auto p-0">
              <Link href="/chat">{t('viewAll')}</Link>
            </Button>
          </div>
        </CardHeader>
        <Separator />
        <CardContent className="pt-3">
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 size={16} className="animate-spin text-muted-foreground" />
            </div>
          ) : recent.length === 0 ? (
            <div className="text-center py-8 space-y-2">
              <Clock size={24} className="mx-auto text-muted-foreground/30" />
              <p className="text-xs font-mono text-muted-foreground/50">{t('noChats')}</p>
              <Button variant="link" size="sm" asChild className="text-[10px] font-mono">
                <Link href="/chat">{t('startFirst')}</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-1">
              {recent.map((s) => (
                <Link
                  key={s.id}
                  href="/chat"
                  className="flex items-center justify-between px-3 py-2 rounded-md hover:bg-accent transition-colors group"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <MessageSquare size={12} className="text-muted-foreground/40 flex-shrink-0" />
                    <span className="text-xs font-mono text-foreground truncate group-hover:text-primary transition-colors">
                      {s.title || t('unnamed')}
                    </span>
                    <Badge variant="secondary" className="text-[9px] px-1 py-0 h-4 shrink-0">
                      {t('msgCount', { n: s.messageCount })}
                    </Badge>
                  </div>
                  <span className="text-[9px] font-mono text-muted-foreground/40 flex-shrink-0 ml-2">{timeAgo(s.updatedAt)}</span>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
