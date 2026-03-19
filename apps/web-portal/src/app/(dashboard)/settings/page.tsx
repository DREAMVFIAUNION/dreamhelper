'use client'

import { useState, useEffect, useCallback, type FormEvent } from 'react'
import { useAuth } from '@/lib/auth/AuthProvider'
import { useTranslations } from 'next-intl'
import { Bell, BellOff, Download, Trash2, AlertTriangle, Bot, Globe } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'

const STYLE_KEYS = ['default', 'concise', 'detailed', 'professional', 'casual'] as const

function StyleSettingsSection() {
  const t = useTranslations('settings')
  const [style, setStyle] = useState('default')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('dreamhelp_style')
    if (stored) setStyle(stored)
  }, [])

  function handleChange(value: string) {
    setStyle(value)
    localStorage.setItem('dreamhelp_style', value)
    setSaved(true)
    setTimeout(() => setSaved(false), 1500)
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-mono">{t('style')}</CardTitle>
          {saved && (
            <Badge variant="success" className="text-[9px] px-1.5 py-0 h-5 animate-pulse">{t('saved')}</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {STYLE_KEYS.map((key) => {
            const label = t(`style${key.charAt(0).toUpperCase()}${key.slice(1)}` as any)
            const desc = t(`style${key.charAt(0).toUpperCase()}${key.slice(1)}Desc` as any)
            return (
              <button
                key={key}
                onClick={() => handleChange(key)}
                className={cn(
                  'text-left px-3 py-2.5 border text-xs font-mono transition-all rounded-md',
                  style === key
                    ? 'bg-primary/10 border-primary/40 text-primary'
                    : 'bg-secondary border-border text-foreground hover:border-primary/20'
                )}
              >
                <div className="font-bold">{label}</div>
                <div className="text-[10px] text-muted-foreground mt-0.5">{desc}</div>
              </button>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

function ChangePasswordSection() {
  const t = useTranslations('settings')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errors, setErrors] = useState<string[]>([])
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErrors([])
    setSuccess('')

    const errs: string[] = []
    if (!currentPassword) errs.push('请填写当前密码')
    if (newPassword.length < 8) errs.push('新密码至少 8 位')
    if (!/[A-Z]/.test(newPassword)) errs.push('新密码需包含大写字母')
    if (!/[a-z]/.test(newPassword)) errs.push('新密码需包含小写字母')
    if (!/\d/.test(newPassword)) errs.push('新密码需包含数字')
    if (newPassword !== confirmPassword) errs.push('两次密码不一致')

    if (errs.length > 0) {
      setErrors(errs)
      return
    }

    setSubmitting(true)
    try {
      const res = await fetch('/api/auth/password', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ currentPassword, newPassword }),
      })
      const data = (await res.json()) as { success: boolean; errors?: string[]; message?: string }

      if (data.success) {
        setSuccess('密码修改成功')
        setCurrentPassword('')
        setNewPassword('')
        setConfirmPassword('')
      } else {
        setErrors(data.errors ?? ['修改失败'])
      }
    } catch {
      setErrors(['网络错误'])
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-mono">{t('changePassword')}</CardTitle>
      </CardHeader>
      <CardContent>
        {errors.length > 0 && (
          <div className="mb-4 p-3 bg-destructive/10 border border-destructive/30 text-destructive text-xs font-mono rounded-md">
            {errors.map((err, i) => (
              <div key={i}>⚠ {err}</div>
            ))}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono rounded-md">
            ✓ {success}
          </div>
        )}

        <form className="space-y-3 max-w-sm" onSubmit={handleSubmit}>
          <div className="space-y-1.5">
            <Label className="text-[10px] font-mono text-muted-foreground tracking-widest">{t('currentPassword')}</Label>
            <Input type="password" placeholder="••••••••" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} disabled={submitting} className="font-mono" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-[10px] font-mono text-muted-foreground tracking-widest">{t('newPassword')}</Label>
            <Input type="password" placeholder="••••••••" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} disabled={submitting} className="font-mono" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-[10px] font-mono text-muted-foreground tracking-widest">{t('confirmPassword')}</Label>
            <Input type="password" placeholder="••••••••" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} disabled={submitting} className="font-mono" />
          </div>
          <Button type="submit" disabled={submitting} size="sm" className="font-mono">
            {t('changePassword')}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

interface ModelInfo {
  id: string
  provider: string
}

const PROVIDER_LABELS: Record<string, string> = {
  minimax: 'MiniMax',
  openai: 'OpenAI',
  deepseek: 'DeepSeek',
}

function ModelSettingsSection() {
  const t = useTranslations('settings')
  const [model, setModel] = useState('')
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('dreamhelp_model')
    if (stored) setModel(stored)

    fetch('/api/chat/models')
      .then((r) => r.json())
      .then((d: { models?: ModelInfo[] }) => setModels(d.models ?? []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  function handleChange(value: string) {
    setModel(value)
    localStorage.setItem('dreamhelp_model', value)
    setSaved(true)
    setTimeout(() => setSaved(false), 1500)
  }

  const grouped = models.reduce<Record<string, ModelInfo[]>>((acc, m) => {
    const key = m.provider
    if (!acc[key]) acc[key] = []
    acc[key]!.push(m)
    return acc
  }, {})

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot size={14} className="text-primary" />
            <CardTitle className="text-sm font-mono">{t('defaultModel')}</CardTitle>
          </div>
          {saved && (
            <Badge variant="success" className="text-[9px] px-1.5 py-0 h-5 animate-pulse">{t('saved')}</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <p className="text-[10px] font-mono text-muted-foreground">{t('loadingModels')}</p>
        ) : models.length === 0 ? (
          <p className="text-[10px] font-mono text-muted-foreground">{t('noModels')}</p>
        ) : (
          <div className="space-y-3">
            {Object.entries(grouped).map(([provider, providerModels]) => (
              <div key={provider}>
                <p className="text-[10px] font-mono text-muted-foreground mb-1.5 tracking-widest">
                  {PROVIDER_LABELS[provider] ?? provider}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                  {providerModels.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => handleChange(m.id)}
                      className={cn(
                        'text-left px-3 py-2 border text-xs font-mono transition-all rounded-md',
                        model === m.id
                          ? 'bg-primary/10 border-primary/40 text-primary'
                          : 'bg-secondary border-border text-foreground hover:border-primary/20'
                      )}
                    >
                      {m.id}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

const LOCALE_OPTIONS = [
  { value: 'zh-CN', label: '简体中文', flag: '🇨🇳' },
  { value: 'en', label: 'English', flag: '🇺🇸' },
] as const

function LanguageSettingsSection() {
  const t = useTranslations('settings')
  const [locale, setLocale] = useState('zh-CN')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const cookie = document.cookie.split('; ').find((c) => c.startsWith('locale='))
    if (cookie) setLocale(cookie.split('=')[1] ?? 'zh-CN')
  }, [])

  function handleChange(value: string) {
    setLocale(value)
    document.cookie = `locale=${value}; path=/; max-age=31536000`
    setSaved(true)
    setTimeout(() => {
      setSaved(false)
      window.location.reload()
    }, 500)
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe size={14} className="text-muted-foreground" />
            <CardTitle className="text-sm font-mono">{t('language')}</CardTitle>
          </div>
          {saved && (
            <Badge variant="success" className="text-[9px] px-1.5 py-0 h-5 animate-pulse">✓ saved</Badge>
          )}
        </div>
        <CardDescription className="text-[10px] font-mono">{t('languageDesc')}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2">
          {LOCALE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleChange(opt.value)}
              className={cn(
                'flex items-center gap-2 px-3 py-2.5 border text-xs font-mono transition-all rounded-md',
                locale === opt.value
                  ? 'bg-primary/10 border-primary/40 text-primary'
                  : 'bg-secondary border-border text-foreground hover:border-primary/20'
              )}
            >
              <span>{opt.flag}</span>
              <span className="font-bold">{opt.label}</span>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function NotificationSettingsSection() {
  const t = useTranslations('settings')
  const [proactive, setProactive] = useState(true)
  const [sound, setSound] = useState(true)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('dreamhelp_notifications')
    if (stored) {
      try {
        const val = JSON.parse(stored) as { proactive?: boolean; sound?: boolean }
        if (val.proactive !== undefined) setProactive(val.proactive)
        if (val.sound !== undefined) setSound(val.sound)
      } catch { /* ignore */ }
    }
  }, [])

  function save(p: boolean, s: boolean) {
    setProactive(p)
    setSound(s)
    localStorage.setItem('dreamhelp_notifications', JSON.stringify({ proactive: p, sound: s }))
    setSaved(true)
    setTimeout(() => setSaved(false), 1500)
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-mono">{t('notificationPrefs')}</CardTitle>
          {saved && (
            <Badge variant="success" className="text-[9px] px-1.5 py-0 h-5 animate-pulse">{t('saved')}</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <label className="flex items-center justify-between cursor-pointer group">
          <div className="flex items-center gap-2 text-xs font-mono text-foreground">
            {proactive ? <Bell size={14} className="text-primary" /> : <BellOff size={14} className="text-muted-foreground" />}
            {t('proactiveNotif')}
          </div>
          <button
            onClick={() => save(!proactive, sound)}
            className={cn('w-10 h-5 rounded-full transition-colors relative', proactive ? 'bg-primary' : 'bg-secondary border border-border')}
          >
            <span className={cn('absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all', proactive ? 'left-5' : 'left-0.5')} />
          </button>
        </label>
        <label className="flex items-center justify-between cursor-pointer group">
          <span className="text-xs font-mono text-foreground">{t('notifSound')}</span>
          <button
            onClick={() => save(proactive, !sound)}
            className={cn('w-10 h-5 rounded-full transition-colors relative', sound ? 'bg-primary' : 'bg-secondary border border-border')}
          >
            <span className={cn('absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all', sound ? 'left-5' : 'left-0.5')} />
          </button>
        </label>
      </CardContent>
    </Card>
  )
}

function DataExportSection() {
  const t = useTranslations('settings')
  const [exporting, setExporting] = useState(false)

  const handleExport = useCallback(async (format: 'json' | 'markdown') => {
    setExporting(true)
    try {
      const res = await fetch(`/api/user/export?format=${format}`, { credentials: 'include' })
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `dreamhelp-export-${Date.now()}.${format === 'json' ? 'json' : 'md'}`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('导出失败，请稍后重试')
    } finally {
      setExporting(false)
    }
  }, [])

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-mono">{t('dataExport')}</CardTitle>
        <CardDescription className="text-[10px] font-mono">{t('exportDesc')}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => handleExport('json')} disabled={exporting} className="font-mono text-xs gap-1.5">
            <Download size={12} />
            {t('exportJSON')}
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('markdown')} disabled={exporting} className="font-mono text-xs gap-1.5">
            <Download size={12} />
            {t('exportMarkdown')}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function DangerZoneSection() {
  const t = useTranslations('settings')
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function handleDeleteChats() {
    if (!confirmDelete) {
      setConfirmDelete(true)
      return
    }
    setDeleting(true)
    try {
      const res = await fetch('/api/user/chats', { method: 'DELETE', credentials: 'include' })
      const data = (await res.json()) as { success: boolean }
      if (data.success) {
        alert('所有对话已删除')
        setConfirmDelete(false)
      } else {
        alert('删除失败')
      }
    } catch {
      alert('网络错误')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <Card className="border-destructive/20">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle size={14} className="text-destructive" />
          <CardTitle className="text-sm font-mono text-destructive">{t('dangerZone')}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-mono text-foreground">{t('deleteAllChats')}</p>
            <p className="text-[10px] font-mono text-muted-foreground">{t('deleteAllChatsDesc')}</p>
          </div>
          <Button
            variant={confirmDelete ? 'destructive' : 'outline'}
            size="sm"
            onClick={handleDeleteChats}
            disabled={deleting}
            className="font-mono text-xs gap-1.5"
          >
            <Trash2 size={12} />
            {confirmDelete ? t('confirmDelete') : t('deleteAllChats')}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default function SettingsPage() {
  const { user } = useAuth()
  const t = useTranslations('settings')
  const tTier = useTranslations('tier')

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-8 bg-primary rounded-full shadow-[0_0_8px_hsl(var(--primary)/0.4)]" />
        <div>
          <h1 className="font-display text-xl font-bold text-foreground tracking-wider">{t('title')}</h1>
          <p className="text-xs font-mono text-muted-foreground mt-0.5">{t('subtitle')}</p>
        </div>
      </div>

      <div className="space-y-6 max-w-2xl">
        {/* 账户信息 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono">{t('accountInfo')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex items-center gap-3">
                <span className="text-muted-foreground w-16">{t('email')}</span>
                <span className="text-foreground">{user?.email ?? '—'}</span>
                {user && !user.emailVerified && (
                  <Badge variant="warning" className="text-[9px] px-1.5 py-0 h-4">{t('unverified')}</Badge>
                )}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-muted-foreground w-16">{t('username')}</span>
                <span className="text-foreground">{user?.username ?? '—'}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-muted-foreground w-16">{t('level')}</span>
                <Badge variant="cyber" className="text-[9px] px-1.5 py-0 h-4">
                  {user?.tierLevel === 0 ? tTier('free') : user?.tierLevel === 1 ? tTier('vip') : user?.tierLevel === 2 ? tTier('enterprise') : user?.tierLevel && user.tierLevel >= 9 ? tTier('admin') : '—'}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI 回复风格 */}
        <StyleSettingsSection />

        {/* 默认模型 */}
        <ModelSettingsSection />

        {/* 语言切换 */}
        <LanguageSettingsSection />

        {/* 通知偏好 */}
        <NotificationSettingsSection />

        {/* 修改密码 */}
        <ChangePasswordSection />

        {/* 数据导出 */}
        <DataExportSection />

        {/* 危险区域 */}
        <DangerZoneSection />
      </div>
    </div>
  )
}
