'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useState, type FormEvent } from 'react'

function PasswordStrength({ password }: { password: string }) {
  let score = 0
  if (password.length >= 8) score++
  if (/[a-z]/.test(password)) score++
  if (/[A-Z]/.test(password)) score++
  if (/\d/.test(password)) score++
  if (/[^a-zA-Z\d]/.test(password)) score++

  const labels = ['', '弱', '较弱', '中等', '较强', '强']
  const colors = ['', 'bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-cyan-500', 'bg-emerald-400']

  if (!password) return null

  return (
    <div className="flex items-center gap-2 mt-1.5">
      <div className="flex gap-0.5 flex-1">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-colors ${i <= score ? colors[score] : 'bg-secondary'}`}
          />
        ))}
      </div>
      <span className="text-[10px] font-mono text-muted-foreground">{labels[score]}</span>
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordForm />
    </Suspense>
  )
}

function ResetPasswordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token') ?? ''

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errors, setErrors] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErrors([])

    const errs: string[] = []
    if (!token) errs.push('重置令牌缺失，请从邮件中的链接访问')
    if (password.length < 8) errs.push('密码至少 8 位')
    if (!/[A-Z]/.test(password)) errs.push('密码需包含大写字母')
    if (!/[a-z]/.test(password)) errs.push('密码需包含小写字母')
    if (!/\d/.test(password)) errs.push('密码需包含数字')
    if (password !== confirmPassword) errs.push('两次密码不一致')

    if (errs.length > 0) {
      setErrors(errs)
      return
    }

    setSubmitting(true)
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password }),
      })
      const data = (await res.json()) as { success: boolean; errors?: string[]; message?: string }

      if (data.success) {
        setSuccess(true)
        setTimeout(() => router.push('/login'), 3000)
      } else {
        setErrors(data.errors ?? ['重置失败'])
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
                NEW PASSWORD
              </h1>
              <p className="font-mono text-[10px] text-muted-foreground tracking-widest mt-1">
                设置您的新密码
              </p>
            </div>
            <div className="flex items-center gap-3 w-full">
              <div className="flex-1 h-px bg-gradient-to-r from-transparent to-primary/30" />
              <span className="font-mono text-[10px] text-muted-foreground tracking-widest">PASSWORD RESET</span>
              <div className="flex-1 h-px bg-gradient-to-l from-transparent to-primary/30" />
            </div>
          </div>

          {success ? (
            /* ═══ 重置成功 ═══ */
            <div className="space-y-4">
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono rounded-md">
                <p>✓ 密码重置成功！</p>
                <p className="mt-1 text-muted-foreground">3 秒后自动跳转到登录页...</p>
              </div>
              <Link
                href="/login"
                className="block w-full py-3 bg-primary text-primary-foreground font-mono font-bold text-sm text-center shadow-[0_0_12px_hsl(var(--primary)/0.3)] hover:bg-primary/90 hover:shadow-[0_0_16px_hsl(var(--primary)/0.4)] active:scale-[0.98] transition-all duration-150 rounded-md"
              >
                ▶ 立即登录
              </Link>
            </div>
          ) : !token ? (
            /* ═══ 无 Token ═══ */
            <div className="space-y-4">
              <div className="p-4 bg-destructive/10 border border-destructive/30 text-destructive text-xs font-mono rounded-md">
                ⚠ 重置链接无效或已过期，请重新申请密码重置。
              </div>
              <Link
                href="/forgot"
                className="block w-full py-3 bg-primary text-primary-foreground font-mono font-bold text-sm text-center shadow-[0_0_12px_hsl(var(--primary)/0.3)] hover:bg-primary/90 hover:shadow-[0_0_16px_hsl(var(--primary)/0.4)] active:scale-[0.98] transition-all duration-150 rounded-md"
              >
                ▶ 重新申请
              </Link>
            </div>
          ) : (
            /* ═══ 设置新密码表单 ═══ */
            <>
              {errors.length > 0 && (
                <div className="mb-4 p-3 bg-destructive/10 border border-destructive/30 text-destructive text-xs font-mono rounded-md">
                  {errors.map((err, i) => (
                    <div key={i}>⚠ {err}</div>
                  ))}
                </div>
              )}

              <form className="space-y-3" onSubmit={handleSubmit}>
                <div className="space-y-1">
                  <label className="block text-[10px] font-mono text-muted-foreground tracking-widest">
                    新密码 / NEW PASSWORD
                  </label>
                  <input
                    type="password"
                    placeholder="至少 8 位，含大小写+数字"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={submitting}
                    className={inputCls}
                  />
                  <PasswordStrength password={password} />
                </div>

                <div className="space-y-1">
                  <label className="block text-[10px] font-mono text-muted-foreground tracking-widest">
                    确认密码 / CONFIRM
                  </label>
                  <input
                    type="password"
                    placeholder="再次输入新密码"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    disabled={submitting}
                    className={inputCls}
                  />
                  {confirmPassword && password !== confirmPassword && (
                    <p className="text-[10px] font-mono text-destructive mt-0.5">密码不一致</p>
                  )}
                  {confirmPassword && password === confirmPassword && confirmPassword.length > 0 && (
                    <p className="text-[10px] font-mono text-emerald-400 mt-0.5">✓ 密码匹配</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full mt-4 py-3 bg-primary text-primary-foreground font-mono font-bold text-sm shadow-[0_0_12px_hsl(var(--primary)/0.3)] hover:bg-primary/90 hover:shadow-[0_0_16px_hsl(var(--primary)/0.4)] active:scale-[0.98] transition-all duration-150 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? '▶ 重置中...' : '▶ 重置密码'}
                </button>
              </form>
            </>
          )}

          {/* 底部链接 */}
          <div className="mt-6 flex items-center justify-between text-[10px] font-mono">
            <Link href="/login" className="text-muted-foreground hover:text-primary transition-colors tracking-wider">
              ▸ 返回登录
            </Link>
            <Link href="/forgot" className="text-muted-foreground hover:text-secondary-foreground transition-colors tracking-wider">
              ▸ 重新申请
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
