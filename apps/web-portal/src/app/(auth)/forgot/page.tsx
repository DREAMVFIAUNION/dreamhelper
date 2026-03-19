'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useState, type FormEvent } from 'react'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [errors, setErrors] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)
  const [devToken, setDevToken] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErrors([])

    if (!email) {
      setErrors(['请填写邮箱'])
      return
    }

    setSubmitting(true)
    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      const data = (await res.json()) as {
        success: boolean
        message?: string
        errors?: string[]
        __dev_token?: string
        __dev_code?: string
      }

      if (data.success) {
        setSent(true)
        if (data.__dev_token) {
          setDevToken(data.__dev_token)
        }
      } else {
        setErrors(data.errors ?? ['请求失败'])
      }
    } catch {
      setErrors(['网络错误，请稍后重试'])
    } finally {
      setSubmitting(false)
    }
  }

  const inputCls =
    'w-full bg-secondary border border-border px-3 py-2.5 text-sm font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 focus:shadow-[0_0_8px_hsl(var(--primary)/0.2)] transition-all duration-200 rounded-md disabled:opacity-50'

  return (
    <div className="min-h-screen bg-background flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-grid-cyber opacity-20 pointer-events-none" />
      <div className="absolute inset-0 bg-scanline opacity-30 pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary/5 blur-[120px] pointer-events-none" />

      <div className="relative z-10 w-full max-w-md mx-4 bg-card border border-border shadow-[0_0_20px_hsl(var(--primary)/0.15)] rounded-lg">
        <div className="h-1 bg-gradient-to-r from-transparent via-primary to-transparent" />
        <div className="px-8 py-10">
          {/* LOGO */}
          <div className="flex flex-col items-center gap-3 mb-8">
            <div className="relative w-16 h-16 drop-shadow-[0_0_20px_hsl(var(--primary)/0.5)]">
              <Image src="/logo/logo.png" alt="DREAMVFIA" fill sizes="64px" className="object-contain" priority />
            </div>
            <div className="text-center">
              <h1 className="font-display text-xl font-black tracking-[0.3em] text-primary drop-shadow-[0_0_10px_hsl(var(--primary)/0.5)]">
                RESET ACCESS
              </h1>
              <p className="font-mono text-[10px] text-muted-foreground tracking-widest mt-1">
                找回您的 DREAMVFIA 密码
              </p>
            </div>
            <div className="flex items-center gap-3 w-full">
              <div className="flex-1 h-px bg-gradient-to-r from-transparent to-primary/30" />
              <span className="font-mono text-[10px] text-muted-foreground tracking-widest">PASSWORD RECOVERY</span>
              <div className="flex-1 h-px bg-gradient-to-l from-transparent to-primary/30" />
            </div>
          </div>

          {sent ? (
            /* ═══ 发送成功状态 ═══ */
            <div className="space-y-4">
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono rounded-md">
                <p>✓ 如果该邮箱已注册，重置链接已发送到您的邮箱。</p>
                <p className="mt-1 text-muted-foreground">请检查收件箱（含垃圾邮件），链接 30 分钟内有效。</p>
              </div>

              {/* 开发模式: 显示 token 以便直接跳转 */}
              {devToken && (
                <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 text-yellow-500 text-[10px] font-mono rounded-md">
                  <p className="font-bold mb-1">⚠ DEV MODE — 重置链接:</p>
                  <Link
                    href={`/reset?token=${devToken}`}
                    className="text-primary hover:underline break-all"
                  >
                    /reset?token={devToken.slice(0, 16)}...
                  </Link>
                </div>
              )}

              <div className="flex flex-col gap-2">
                <Link
                  href="/login"
                  className="w-full py-3 bg-primary text-primary-foreground font-mono font-bold text-sm text-center shadow-[0_0_12px_hsl(var(--primary)/0.3)] hover:bg-primary/90 hover:shadow-[0_0_16px_hsl(var(--primary)/0.4)] active:scale-[0.98] transition-all duration-150 rounded-md">
                  ▶ 返回登录
                </Link>
                <button
                  type="button"
                  onClick={() => { setSent(false); setDevToken('') }}
                  className="w-full py-2.5 bg-secondary border border-border text-xs font-mono text-muted-foreground hover:text-primary hover:border-primary/50 transition-all rounded-md">
                  重新发送
                </button>
              </div>
            </div>
          ) : (
            /* ═══ 输入邮箱表单 ═══ */
            <>
              {errors.length > 0 && (
                <div className="mb-4 p-3 bg-destructive/10 border border-destructive/30 text-destructive text-xs font-mono rounded-md">
                  {errors.map((err, i) => (
                    <div key={i}>⚠ {err}</div>
                  ))}
                </div>
              )}

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="space-y-1.5">
                  <label className="block text-[10px] font-mono text-muted-foreground tracking-widest">
                    注册邮箱 / EMAIL
                  </label>
                  <input
                    type="email"
                    placeholder="user@dreamvfia.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={submitting}
                    className={inputCls}
                  />
                  <p className="text-[10px] font-mono text-muted-foreground/60 mt-1">
                    输入您注册时使用的邮箱，我们将发送密码重置链接
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full mt-2 py-3 bg-primary text-primary-foreground font-mono font-bold text-sm shadow-[0_0_12px_hsl(var(--primary)/0.3)] hover:bg-primary/90 hover:shadow-[0_0_16px_hsl(var(--primary)/0.4)] active:scale-[0.98] transition-all duration-150 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? '▶ 发送中...' : '▶ 发送重置链接'}
                </button>
              </form>
            </>
          )}

          {/* 底部链接 */}
          <div className="mt-6 flex items-center justify-between text-[10px] font-mono">
            <Link href="/login" className="text-muted-foreground hover:text-primary transition-colors tracking-wider">
              ▸ 返回登录
            </Link>
            <Link href="/register" className="text-muted-foreground hover:text-secondary-foreground transition-colors tracking-wider">
              ▸ 注册账号
            </Link>
          </div>
        </div>
        <div className="h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
      </div>

      <div className="absolute top-4 left-4 font-mono text-[10px] text-muted-foreground/40 tracking-widest">DREAMVFIA.AI · v3.0.0</div>
      <div className="absolute bottom-4 right-4 font-mono text-[10px] text-muted-foreground/40 tracking-widest">© 2026 DREAMVFIA CORP.</div>
    </div>
  )
}
