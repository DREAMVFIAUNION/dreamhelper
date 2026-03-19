'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import DOMPurify from 'dompurify'
import { Button } from '@/components/ui/button'
import { Send, History, Eye, EyeOff, Users, Mail, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react'

// ═══ 邮件模板 ═══

const TEMPLATES = [
  {
    name: '产品更新',
    subject: '【DREAMVFIA】梦帮小助新版本发布',
    html: `<div style="font-family: monospace; background: #0a0a14; color: #e0e0e0; padding: 32px; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #fe0000; letter-spacing: 0.1em;">DREAMVFIA · 产品更新</h2>
  <p>尊敬的用户，</p>
  <p>梦帮小助发布了新版本，为您带来以下更新：</p>
  <ul style="color: #ccc; line-height: 1.8;">
    <li>🧠 三脑并行架构优化</li>
    <li>⚡ 新增技能模块</li>
    <li>🔒 安全性增强</li>
  </ul>
  <a href="https://dreamvfia.com/changelog" style="display: inline-block; padding: 12px 24px; background: #fe0000; color: #000; font-weight: bold; text-decoration: none; letter-spacing: 0.1em; margin: 16px 0;">查看详情</a>
  <hr style="border-color: #333; margin: 24px 0;" />
  <p style="color: #555; font-size: 10px;">此邮件由 DREAMVFIA 系统发送。如不希望收到此类邮件，请联系 support@dreamvfia.com。</p>
</div>`,
  },
  {
    name: '活动通知',
    subject: '【DREAMVFIA】限时活动邀请',
    html: `<div style="font-family: monospace; background: #0a0a14; color: #e0e0e0; padding: 32px; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #fe0000; letter-spacing: 0.1em;">DREAMVFIA · 限时活动</h2>
  <p>尊敬的用户，</p>
  <p>我们正在举办限时活动，诚邀您参加：</p>
  <div style="background: #1a1a2e; border: 1px solid #fe000040; padding: 16px; margin: 16px 0; text-align: center;">
    <p style="font-size: 20px; color: #fe0000; font-weight: bold;">专业版限时优惠 50% OFF</p>
    <p style="color: #888;">活动时间：即日起至月底</p>
  </div>
  <a href="https://dreamvfia.com/pricing" style="display: inline-block; padding: 12px 24px; background: #fe0000; color: #000; font-weight: bold; text-decoration: none; letter-spacing: 0.1em; margin: 16px 0;">立即参加</a>
  <hr style="border-color: #333; margin: 24px 0;" />
  <p style="color: #555; font-size: 10px;">此邮件由 DREAMVFIA 系统发送。如不希望收到此类邮件，请联系 support@dreamvfia.com。</p>
</div>`,
  },
  {
    name: '新功能公告',
    subject: '【DREAMVFIA】新功能上线通知',
    html: `<div style="font-family: monospace; background: #0a0a14; color: #e0e0e0; padding: 32px; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #fe0000; letter-spacing: 0.1em;">DREAMVFIA · 新功能上线</h2>
  <p>尊敬的用户，</p>
  <p>梦帮小助上线了全新功能：</p>
  <div style="background: #1a1a2e; border: 1px solid #fe000040; padding: 16px; margin: 16px 0;">
    <h3 style="color: #fe0000; margin-bottom: 8px;">🚀 功能名称</h3>
    <p style="color: #ccc;">功能描述内容，请在此修改。</p>
  </div>
  <p>立即登录体验！</p>
  <a href="https://dreamvfia.com" style="display: inline-block; padding: 12px 24px; background: #fe0000; color: #000; font-weight: bold; text-decoration: none; letter-spacing: 0.1em; margin: 16px 0;">开始使用</a>
  <hr style="border-color: #333; margin: 24px 0;" />
  <p style="color: #555; font-size: 10px;">此邮件由 DREAMVFIA 系统发送。如不希望收到此类邮件，请联系 support@dreamvfia.com。</p>
</div>`,
  },
]

// ═══ 类型 ═══

interface EmailLog {
  id: string
  subject: string
  recipientCount: number
  sent: number
  failed: number
  sentAt: string
}

// ═══ 页面 ═══

export default function AdminEmailPage() {
  // 表单状态
  const [sendType, setSendType] = useState<'single' | 'all_users'>('single')
  const [toInput, setToInput] = useState('')
  const [subject, setSubject] = useState('')
  const [html, setHtml] = useState('')
  const [showPreview, setShowPreview] = useState(false)

  // 发送状态
  const [sending, setSending] = useState(false)
  const [sendResult, setSendResult] = useState<{ success: boolean; message: string } | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)

  // 历史记录
  const [logs, setLogs] = useState<EmailLog[]>([])
  const [logsLoading, setLogsLoading] = useState(true)

  const fetchLogs = useCallback(async () => {
    setLogsLoading(true)
    try {
      const res = await fetch('/api/admin/email/history', { credentials: 'include' })
      const data = await res.json()
      if (data.success) setLogs(data.logs ?? [])
    } catch { /* ignore */ }
    finally { setLogsLoading(false) }
  }, [])

  useEffect(() => { void fetchLogs() }, [fetchLogs])

  function applyTemplate(idx: number) {
    const t = TEMPLATES[idx]
    if (!t) return
    setSubject(t.subject)
    setHtml(t.html)
  }

  async function handleSend() {
    setConfirmOpen(false)
    setSending(true)
    setSendResult(null)

    const recipients = sendType === 'all_users'
      ? []
      : toInput.split(/[,;\n]+/).map((s) => s.trim()).filter(Boolean)

    if (sendType === 'single' && recipients.length === 0) {
      setSendResult({ success: false, message: '请填写收件人邮箱' })
      setSending(false)
      return
    }

    try {
      const res = await fetch('/api/admin/email/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          to: recipients,
          subject,
          html,
          sendType,
        }),
      })
      const data = await res.json()
      if (data.success) {
        const d = data.data
        setSendResult({ success: true, message: `发送完成：${d.sent ?? 1} 成功，${d.failed ?? 0} 失败` })
        void fetchLogs()
      } else {
        setSendResult({ success: false, message: data.error || '发送失败' })
      }
    } catch {
      setSendResult({ success: false, message: '网络错误' })
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div>
        <h1 className="text-lg font-mono font-bold text-foreground flex items-center gap-2">
          <Mail size={18} className="text-primary" />
          邮件营销
        </h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">
          仅超级管理员可用 · Resend API · 免费 100 封/天
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：撰写区 */}
        <div className="space-y-4">
          {/* 发送类型 */}
          <div className="bg-card border border-border rounded-md p-4 space-y-3">
            <label className="text-xs font-mono font-bold text-foreground">发送对象</label>
            <div className="flex gap-2">
              <button
                onClick={() => setSendType('single')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded-md border transition-colors ${
                  sendType === 'single'
                    ? 'bg-primary/10 border-primary/40 text-primary'
                    : 'bg-secondary border-border text-muted-foreground hover:text-foreground'
                }`}
              >
                <Mail size={12} /> 指定邮箱
              </button>
              <button
                onClick={() => setSendType('all_users')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded-md border transition-colors ${
                  sendType === 'all_users'
                    ? 'bg-primary/10 border-primary/40 text-primary'
                    : 'bg-secondary border-border text-muted-foreground hover:text-foreground'
                }`}
              >
                <Users size={12} /> 全体用户
              </button>
            </div>

            {sendType === 'single' && (
              <textarea
                placeholder="收件人邮箱（多个用逗号或换行分隔）"
                value={toInput}
                onChange={(e) => setToInput(e.target.value)}
                rows={2}
                className="w-full bg-secondary border border-border px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 rounded-md resize-none"
              />
            )}

            {sendType === 'all_users' && (
              <div className="flex items-center gap-2 px-3 py-2 bg-amber-500/10 border border-amber-500/30 rounded-md">
                <AlertTriangle size={14} className="text-amber-500 flex-shrink-0" />
                <span className="text-xs text-amber-400">将发送给所有已验证邮箱的活跃用户</span>
              </div>
            )}
          </div>

          {/* 模板选择 */}
          <div className="bg-card border border-border rounded-md p-4 space-y-3">
            <label className="text-xs font-mono font-bold text-foreground">快速模板</label>
            <div className="flex gap-2 flex-wrap">
              {TEMPLATES.map((t, i) => (
                <button
                  key={t.name}
                  onClick={() => applyTemplate(i)}
                  className="px-3 py-1.5 text-xs font-mono bg-secondary border border-border rounded-md text-muted-foreground hover:text-primary hover:border-primary/40 transition-colors"
                >
                  {t.name}
                </button>
              ))}
            </div>
          </div>

          {/* 主题 */}
          <div className="bg-card border border-border rounded-md p-4 space-y-3">
            <label className="text-xs font-mono font-bold text-foreground">邮件主题</label>
            <input
              type="text"
              placeholder="输入邮件主题..."
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full bg-secondary border border-border px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 rounded-md"
            />
          </div>

          {/* HTML 内容编辑器 */}
          <div className="bg-card border border-border rounded-md p-4 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono font-bold text-foreground">邮件内容 (HTML)</label>
              <button
                onClick={() => setShowPreview(!showPreview)}
                className="flex items-center gap-1 text-[10px] font-mono text-muted-foreground hover:text-primary transition-colors"
              >
                {showPreview ? <EyeOff size={12} /> : <Eye size={12} />}
                {showPreview ? '编辑' : '预览'}
              </button>
            </div>

            {showPreview ? (
              <div
                className="w-full min-h-[300px] bg-white rounded-md p-4 text-black overflow-auto"
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }}
              />
            ) : (
              <textarea
                placeholder="粘贴或编写 HTML 邮件内容..."
                value={html}
                onChange={(e) => setHtml(e.target.value)}
                rows={14}
                className="w-full bg-secondary border border-border px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 rounded-md resize-y"
              />
            )}
          </div>

          {/* 发送结果 */}
          {sendResult && (
            <div className={`flex items-center gap-2 px-4 py-3 rounded-md border ${
              sendResult.success
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-destructive/10 border-destructive/30 text-destructive'
            }`}>
              {sendResult.success ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
              <span className="text-xs font-mono">{sendResult.message}</span>
            </div>
          )}

          {/* 发送按钮 */}
          <Button
            onClick={() => setConfirmOpen(true)}
            disabled={sending || !subject.trim() || !html.trim()}
            className="w-full text-xs font-mono font-bold gap-2"
          >
            {sending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            {sending ? '发送中...' : '发送邮件'}
          </Button>
        </div>

        {/* 右侧：发送记录 */}
        <div className="bg-card border border-border rounded-md p-4">
          <div className="flex items-center gap-2 mb-4">
            <History size={14} className="text-primary" />
            <h2 className="text-sm font-mono font-bold text-foreground">发送记录</h2>
          </div>

          {logsLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 size={16} className="animate-spin text-muted-foreground" />
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12">
              <Mail size={24} className="mx-auto mb-2 text-muted-foreground/30" />
              <p className="text-xs text-muted-foreground/50 font-mono">暂无发送记录</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {logs.map((log) => (
                <div key={log.id} className="p-3 bg-secondary border border-border/50 rounded-md">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono font-bold text-foreground truncate max-w-[200px]">{log.subject}</span>
                    <span className="text-[10px] font-mono text-muted-foreground/50 flex-shrink-0">
                      {new Date(log.sentAt).toLocaleString('zh-CN')}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] font-mono">
                    <span className="text-muted-foreground">
                      收件人: {log.recipientCount}
                    </span>
                    <span className="text-emerald-400">
                      成功: {log.sent}
                    </span>
                    {log.failed > 0 && (
                      <span className="text-destructive">
                        失败: {log.failed}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 确认弹窗 */}
      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-card border border-border rounded-md p-6 w-full max-w-md space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle size={18} className="text-amber-500" />
              <h2 className="text-sm font-mono font-bold text-foreground">确认发送</h2>
            </div>
            <div className="text-xs font-mono text-muted-foreground space-y-1">
              <p><strong className="text-foreground">主题：</strong>{subject}</p>
              <p><strong className="text-foreground">发送对象：</strong>{sendType === 'all_users' ? '全体已验证用户' : `${toInput.split(/[,;\n]+/).filter(Boolean).length} 个邮箱`}</p>
            </div>
            <p className="text-xs text-amber-400 font-mono">⚠️ 邮件发送后无法撤回，请确认内容无误。</p>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setConfirmOpen(false)} className="text-xs font-mono">
                取消
              </Button>
              <Button size="sm" onClick={() => void handleSend()} className="text-xs font-mono gap-1">
                <Send size={12} /> 确认发送
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
