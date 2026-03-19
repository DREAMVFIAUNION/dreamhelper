'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useState, type FormEvent } from 'react'
import { useAuth } from '@/lib/auth/AuthProvider'

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  )
}

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErrors([])

    if (!email || !password) {
      setErrors(['请填写邮箱和密码'])
      return
    }

    setSubmitting(true)
    try {
      const result = await login({ email, password })
      if (result.success) {
        const from = searchParams.get('from') || '/overview'
        router.push(from)
      } else {
        setErrors(result.errors ?? ['登录失败'])
      }
    } catch {
      setErrors(['网络错误，请稍后重试'])
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center relative overflow-hidden">
      {/* 背景层 */}
      <div className="absolute inset-0 bg-grid-cyber opacity-20 pointer-events-none" />
      <div className="absolute inset-0 bg-scanline opacity-30 pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary/5 blur-[120px] pointer-events-none" />

      {/* 登录卡片 */}
      <div className="relative z-10 w-full max-w-md mx-4 bg-card border border-border shadow-[0_0_20px_hsl(var(--primary)/0.15)] rounded-lg">
        <div className="h-1 bg-gradient-to-r from-transparent via-primary to-transparent" />
        <div className="px-8 py-10">
          {/* LOGO */}
          <div className="flex flex-col items-center gap-4 mb-10">
            <div className="relative w-20 h-20 drop-shadow-[0_0_20px_hsl(var(--primary)/0.5)]">
              <Image src="/logo/logo.png" alt="DREAMVFIA" fill sizes="80px" className="object-contain" priority />
            </div>
            <div className="text-center">
              <h1 className="font-display text-2xl font-black tracking-[0.3em] text-primary animate-flicker drop-shadow-[0_0_10px_hsl(var(--primary)/0.5)]">
                DREAMVFIA
              </h1>
              <p className="font-mono text-xs text-muted-foreground tracking-widest mt-1">
                梦帮小助 · AI ASSISTANT v3.0
              </p>
            </div>
            <div className="flex items-center gap-3 w-full">
              <div className="flex-1 h-px bg-gradient-to-r from-transparent to-primary/30" />
              <span className="font-mono text-[10px] text-muted-foreground tracking-widest">SYSTEM ACCESS</span>
              <div className="flex-1 h-px bg-gradient-to-l from-transparent to-primary/30" />
            </div>
          </div>

          {/* 错误提示 */}
          {errors.length > 0 && (
            <div role="alert" aria-live="assertive" className="mb-4 p-3 bg-destructive/10 border border-destructive/30 text-destructive text-xs font-mono rounded-md">
              {errors.map((err, i) => (
                <div key={i}>⚠ {err}</div>
              ))}
            </div>
          )}

          {/* 表单 */}
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-1.5">
              <label htmlFor="login-email" className="block text-[10px] font-mono text-muted-foreground tracking-widest">用户标识 / EMAIL</label>
              <input
                id="login-email"
                type="email"
                placeholder="user@dreamvfia.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                disabled={submitting}
                className="w-full bg-secondary border border-border px-3 py-2.5 text-sm font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 focus:shadow-[0_0_8px_hsl(var(--primary)/0.2)] transition-all duration-200 rounded-md disabled:opacity-50"
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="login-password" className="block text-[10px] font-mono text-muted-foreground tracking-widest">访问密钥 / PASSWORD</label>
              <input
                id="login-password"
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                disabled={submitting}
                className="w-full bg-secondary border border-border px-3 py-2.5 text-sm font-mono text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-primary/50 focus:shadow-[0_0_8px_hsl(var(--primary)/0.2)] transition-all duration-200 rounded-md disabled:opacity-50"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full mt-6 py-3 bg-primary text-primary-foreground font-mono font-bold text-sm shadow-[0_0_12px_hsl(var(--primary)/0.3)] hover:bg-primary/90 hover:shadow-[0_0_16px_hsl(var(--primary)/0.4)] active:scale-[0.98] transition-all duration-150 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? '▶ 验证中...' : '▶ 进入系统'}
            </button>
          </form>

          {/* 底部链接 */}
          <div className="mt-6 flex items-center justify-between text-[10px] font-mono">
            <Link href="/register" className="text-muted-foreground hover:text-primary transition-colors tracking-wider">
              ▸ 注册账号
            </Link>
            <Link href="/forgot" className="text-muted-foreground hover:text-primary transition-colors tracking-wider">
              ▸ 忘记密码
            </Link>
            <Link href="/" className="text-muted-foreground hover:text-secondary-foreground transition-colors tracking-wider">
              ▸ 返回首页
            </Link>
          </div>

          <div className="mt-8 text-center">
            <div className="flex items-center justify-center gap-2 text-[10px] font-mono text-muted-foreground/50">
              <div className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
              <span>SYSTEM ONLINE · ENCRYPTED CONNECTION</span>
            </div>
          </div>
        </div>
        <div className="h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
      </div>

      <div className="absolute top-4 left-4 font-mono text-[10px] text-muted-foreground/40 tracking-widest">DREAMVFIA.AI · v3.0.0</div>
      <div className="absolute bottom-4 right-4 font-mono text-[10px] text-muted-foreground/40 tracking-widest">© 2026 DREAMVFIA CORP.</div>
    </div>
  )
}
