'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { Radio, MessageSquare, Send, Building2, RefreshCw, CheckCircle2, XCircle, ExternalLink, Users, Link2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'

interface ChannelMetrics {
  received: number
  replied: number
  errors: number
  lastMessageAt?: string
}

interface ChannelInfo {
  configured: boolean
  metrics: ChannelMetrics
  userMapping?: { count: number }
}

interface ChannelStats {
  channels: {
    wechat: ChannelInfo
    wecom: ChannelInfo
    telegram: ChannelInfo
  }
}

interface ChannelUserMapping {
  id: string
  channel: string
  channelUserId: string
  userId: string
  displayName?: string
  createdAt: string
}

const GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

const CHANNEL_CONFIG = [
  {
    key: 'telegram' as const,
    name: 'Telegram Bot',
    icon: Send,
    color: 'text-sky-400',
    bgColor: 'bg-sky-500/10',
    borderColor: 'border-sky-500/30',
    description: '通过 Telegram Bot 接入，支持文本、图片、贴纸消息',
    setupGuide: '1. 通过 @BotFather 创建 Bot\n2. 获取 Bot Token\n3. 设置环境变量 TELEGRAM_BOT_TOKEN\n4. 配置 Webhook URL',
    docsUrl: 'https://core.telegram.org/bots/api',
  },
  {
    key: 'wechat' as const,
    name: '微信公众号',
    icon: MessageSquare,
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
    description: '通过微信公众号接入，支持文本消息和关注事件',
    setupGuide: '1. 登录微信公众平台\n2. 获取 AppID 和 AppSecret\n3. 设置服务器 URL 和 Token\n4. 配置环境变量',
    docsUrl: 'https://developers.weixin.qq.com/doc/offiaccount/',
  },
  {
    key: 'wecom' as const,
    name: '企业微信',
    icon: Building2,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    description: '通过企业微信应用接入，支持文本消息和事件回调',
    setupGuide: '1. 登录企业微信管理后台\n2. 创建自建应用\n3. 获取 CorpID、Secret、AgentID\n4. 配置回调 URL 和 Token',
    docsUrl: 'https://developer.work.weixin.qq.com/document/',
  },
]

export default function ChannelsPage() {
  const t = useTranslations('channels')
  const tc = useTranslations('common')
  const [stats, setStats] = useState<ChannelStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedChannel, setExpandedChannel] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'channels' | 'users'>('channels')
  const [channelUsers, setChannelUsers] = useState<ChannelUserMapping[]>([])
  const [usersLoading, setUsersLoading] = useState(false)

  const fetchStats = async () => {
    setLoading(true)
    try {
      const resp = await fetch(`${GATEWAY_URL}/api/v1/channels/stats`)
      if (resp.ok) {
        const data = await resp.json()
        setStats(data)
      }
    } catch {
      setStats(null)
    } finally {
      setLoading(false)
    }
  }

  const fetchUsers = async () => {
    setUsersLoading(true)
    try {
      const resp = await fetch(`${GATEWAY_URL}/api/v1/channels/users?limit=100`)
      if (resp.ok) {
        const data = await resp.json()
        setChannelUsers(Array.isArray(data) ? data : [])
      }
    } catch {
      setChannelUsers([])
    } finally {
      setUsersLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  useEffect(() => {
    if (activeTab === 'users') fetchUsers()
  }, [activeTab])

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-1 h-8 bg-primary rounded-full shadow-[0_0_8px_hsl(var(--primary)/0.4)]" />
          <div>
            <h1 className="text-xl font-display font-bold text-foreground">{t('title')}</h1>
            <p className="text-sm text-muted-foreground mt-0.5">{t('subtitle')}</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={activeTab === 'channels' ? fetchStats : fetchUsers}
          disabled={loading || usersLoading}
          className="font-mono text-xs gap-1.5"
        >
          <RefreshCw size={12} className={(loading || usersLoading) ? 'animate-spin' : ''} />
          {t('refresh')}
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'channels' | 'users')}>
        <TabsList>
          <TabsTrigger value="channels" className="text-xs font-mono gap-1.5">
            <Radio size={12} /> {t('channelConfig')}
          </TabsTrigger>
          <TabsTrigger value="users" className="text-xs font-mono gap-1.5">
            <Users size={12} /> {t('connectedUsers')}
            {stats && (
              <Badge variant="secondary" className="ml-1 text-[9px] px-1.5 py-0 h-4">
                {Object.values(stats.channels).reduce((s, c) => s + (c.userMapping?.count || 0), 0)}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

      <TabsContent value="channels" className="space-y-4 mt-4">
      <div className="grid gap-4">
        {CHANNEL_CONFIG.map((ch) => {
          const info = stats?.channels?.[ch.key]
          const configured = info?.configured ?? false
          const metrics = info?.metrics
          const Icon = ch.icon
          const expanded = expandedChannel === ch.key

          return (
            <Card
              key={ch.key}
              className={cn('overflow-hidden transition-all', configured && ch.borderColor)}
            >
              <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-accent/30 transition-colors"
                onClick={() => setExpandedChannel(expanded ? null : ch.key)}
              >
                <div className="flex items-center gap-3">
                  <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', ch.bgColor)}>
                    <Icon size={20} className={ch.color} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-foreground text-sm">{ch.name}</span>
                      <Badge variant={configured ? 'success' : 'secondary'} className="text-[9px] px-1.5 py-0 h-4 gap-1">
                        {configured ? <><CheckCircle2 size={10} /> {t('configured')}</> : <><XCircle size={10} /> {t('notConfigured')}</>}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{ch.description}</p>
                  </div>
                </div>

                {configured && metrics && (
                  <div className="flex items-center gap-4 text-xs text-muted-foreground font-mono">
                    <div className="text-center">
                      <div className="text-foreground font-medium">{metrics.received}</div>
                      <div>{t('received')}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-emerald-400 font-medium">{metrics.replied}</div>
                      <div>{t('replied')}</div>
                    </div>
                    <div className="text-center">
                      <div className={cn('font-medium', metrics.errors > 0 ? 'text-destructive' : 'text-foreground')}>
                        {metrics.errors}
                      </div>
                      <div>{t('errors')}</div>
                    </div>
                  </div>
                )}
              </div>

              {expanded && (
                <div className="px-4 pb-4 pt-0 border-t border-border">
                  <div className="mt-3 space-y-3">
                    <div>
                      <h4 className="text-xs font-mono text-muted-foreground mb-1.5 uppercase tracking-wider">{t('setupSteps')}</h4>
                      <div className="bg-secondary rounded-md p-3 text-xs text-muted-foreground font-mono whitespace-pre-line leading-relaxed">
                        {ch.setupGuide}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <a
                        href={ch.docsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors"
                      >
                        <ExternalLink size={12} /> {t('viewDocs')}
                      </a>
                      {ch.key === 'telegram' && configured && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async (e) => {
                            e.stopPropagation()
                            const webhookUrl = prompt('请输入 Webhook URL (如 https://your-domain.com/webhook/telegram):')
                            if (!webhookUrl) return
                            try {
                              const resp = await fetch(`${GATEWAY_URL}/api/v1/webhook/telegram/setup`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ url: webhookUrl }),
                              })
                              const data = await resp.json()
                              alert(data.ok ? 'Webhook 设置成功!' : 'Webhook 设置失败')
                            } catch {
                              alert('请求失败，请检查 Gateway 服务是否运行')
                            }
                          }}
                          className="text-sky-400 border-sky-500/30 hover:bg-sky-500/10 text-xs font-mono gap-1.5"
                        >
                          <Send size={12} /> {t('setWebhook')}
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </Card>
          )
        })}
      </div>

      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-display font-bold text-foreground mb-2">{t('archInfo')}</h3>
          <div className="text-xs text-muted-foreground leading-relaxed space-y-1.5">
            <p>{t('archFlow')}<span className="text-foreground font-mono">{t('archFlowDetail')}</span></p>
            <p>{t('archDesc1')}</p>
            <p>{t('archDesc2')}</p>
          </div>
        </CardContent>
      </Card>
      </TabsContent>

      <TabsContent value="users" className="space-y-4 mt-4">
        {usersLoading ? (
          <div className="text-center py-12 text-muted-foreground text-sm">{tc('loading')}</div>
        ) : channelUsers.length === 0 ? (
          <div className="text-center py-12">
            <Users size={32} className="mx-auto text-muted-foreground/40 mb-3" />
            <p className="text-muted-foreground text-sm">{t('noUsers')}</p>
            <p className="text-muted-foreground/60 text-xs mt-1">{t('noUsersDesc')}</p>
          </div>
        ) : (
          <Card className="overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-secondary text-muted-foreground font-mono uppercase tracking-wider">
                  <th className="text-left px-4 py-2.5">{t('channel')}</th>
                  <th className="text-left px-4 py-2.5">{t('channelUserId')}</th>
                  <th className="text-left px-4 py-2.5">{t('displayName')}</th>
                  <th className="text-left px-4 py-2.5">{t('systemUserId')}</th>
                  <th className="text-left px-4 py-2.5">{t('connectedAt')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {channelUsers.map((u) => {
                  const chCfg = CHANNEL_CONFIG.find(c => c.key === u.channel)
                  return (
                    <tr key={u.id} className="hover:bg-accent/30 transition-colors">
                      <td className="px-4 py-2.5">
                        <Badge variant="secondary" className={cn('text-[10px] font-mono', chCfg && `${chCfg.bgColor} ${chCfg.color}`)}>
                          {u.channel}
                        </Badge>
                      </td>
                      <td className="px-4 py-2.5 font-mono text-foreground truncate max-w-[180px]">{u.channelUserId}</td>
                      <td className="px-4 py-2.5 text-foreground">{u.displayName || '-'}</td>
                      <td className="px-4 py-2.5 font-mono text-muted-foreground truncate max-w-[140px]">{u.userId.slice(0, 8)}...</td>
                      <td className="px-4 py-2.5 text-muted-foreground">{new Date(u.createdAt).toLocaleDateString('zh-CN')}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </Card>
        )}
      </TabsContent>
      </Tabs>
    </div>
  )
}
