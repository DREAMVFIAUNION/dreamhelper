'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState, useEffect, useRef, type FormEvent } from 'react'
import { useAuth } from '@/lib/auth/AuthProvider'

export default function VerifyEmailPage() {
  const router = useRouter()
  const { user, refreshUser } = useAuth()

  const [code, setCode] = useState('')
  const [errors, setErrors] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [sending, setSending] = useState(false)
  const [cooldown, setCooldown] = useState(0)
  const [devCode, setDevCode] = useState('')
  const cooldownRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // 自动发送验证码
  useEffect(() => {
    if (user && !user.emailVerified) {
      void sendCode()
    }
    return () => {
      if (cooldownRef.current) clearInterval(cooldownRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function startCooldown(seconds: number) {
    setCooldown(seconds)
    if (cooldownRef.current) clearInterval(cooldownRef.current)
    cooldownRef.current = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          if (cooldownRef.current) clearInterval(cooldownRef.current)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }

  async function sendCode() {
    setSending(true)
    setErrors([])
    try {
      const res = await fetch('/api/auth/resend-verify', {
        method: 'POST',
        credentials: 'include',
      })
      const data = (await res.json()) as {
        success: boolean
        errors?: string[]
        __dev_code?: string
      }

      if (data.success) {
        startCooldown(60)
        if (data.__dev_code) {
          setDevCode(data.__dev_code)
        }
      } else {
        if (res.status === 429) {
          // 从错误消息中提取冷却时间
          const match = data.errors?.[0]?.match(/(\d+)/)
          if (match) startCooldown(Number(match[1]))
        }
        setErrors(data.errors ?? ['发送失败'])
      }
    } catch {
      setErrors(['网络错误'])
    } finally {
      setSending(false)
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErrors([])

    if (!code || code.length !== 6) {
      setErrors(['请输入 6 位验证码'])
      return
    }

    setSubmitting(true)
    try {
      const res = await fetch('/api/auth/verify-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ code }),
      })
      const data = (await res.json()) as { success: boolean; errors?: string[] }

      if (data.success) {
        setSuccess(true)
        await refreshUser()
        setTimeout(() => router.push('/overview'), 2000)
      } else {
        setErrors(data.errors ?? ['验证失败'])
      }
    } catch {
      setErrors(['网络错误'])
    } finally {
      setSubmitting(false)
    }
  }

  // 已验证用户重定向
  if (user?.emailVerified) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="text-emerald-400 text-sm font-mono">✓ 邮箱已验证</div>
          <Link href="/overview" className="text-primary text-xs font-mono hover:underline">
            ▸ 进入工作台
          </Link>
        </div>
      </div>
    )
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
                VERIFY EMAIL
              </h1>
              <p className="font-mono text-[10px] text-muted-foreground tracking-widest mt-1">
                验证您的邮箱地址
              </p>
            </div>
            <div className="flex items-center gap-3 w-full">
              <div className="flex-1 h-px bg-gradient-to-r from-transparent to-primary/30" />
              <span className="font-mono text-[10px] text-muted-foreground tracking-widest">EMAIL VERIFICATION</span>
              <div className="flex-1 h-px bg-gradient-to-l from-transparent to-primary/30" />
            </div>
          </div>

          {success ? (
            <div className="space-y-4">
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono rounded-md">
                <p>✓ 邮箱验证成功！</p>
                <p className="mt-1 text-muted-foreground">2 秒后跳转到工作台...</p>
              </div>
              <Link
                href="/overview"
                className="block w-full py-3 bg-primary text-primary-foreground font-mono font-bold text-sm text-center shadow-[0_0_12px_hsl(var(--primary)/0.3)] hover:bg-primary/90 transition-all rounded-md"
              >
                ▶ 进入工作台
              </Link>
            </div>
          ) : (
            <>
              {user && (
                <div className="mb-4 p-3 bg-secondary border border-border text-xs font-mono rounded-md">
                  <span className="text-muted-foreground">验证码已发送到: </span>
                  <span className="text-foreground">{user.email}</span>
                </div>
              )}

              {/* 开发模式验证码 */}
              {devCode && (
                <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 text-yellow-500 text-[10px] font-mono rounded-md">
                  <span className="font-bold">⚠ DEV MODE — 验证码: </span>
                  <span className="text-lg tracking-[0.5em]">{devCode}</span>
                </div>
              )}

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
                    验证码 / VERIFICATION CODE
                  </label>
                  <input
                    type="text"
                    placeholder="输入 6 位验证码"
                    maxLength={6}
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                    disabled={submitting}
                    className={inputCls + ' text-center text-lg tracking-[0.5em]'}
                  />
                </div>

                <button
                  type="submit"
                  disabled={submitting || code.length !== 6}
                  className="w-full py-3 bg-primary text-primary-foreground font-mono font-bold text-sm shadow-[0_0_12px_hsl(var(--primary)/0.3)] hover:bg-primary/90 hover:shadow-[0_0_16px_hsl(var(--primary)/0.4)] active:scale-[0.98] transition-all duration-150 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? '▶ 验证中...' : '▶ 验证邮箱'}
                </button>

                <button
                  type="button"
                  onClick={() => void sendCode()}
                  disabled={sending || cooldown > 0}
                  className="w-full py-2.5 bg-secondary border border-border text-xs font-mono text-muted-foreground hover:text-primary hover:border-primary/50 transition-all rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {cooldown > 0 ? `${cooldown}s 后可重发` : sending ? '发送中...' : '重新发送验证码'}
                </button>
              </form>
            </>
          )}

          <div className="mt-6 flex items-center justify-between text-[10px] font-mono">
            <Link href="/overview" className="text-muted-foreground hover:text-primary transition-colors tracking-wider">
              ▸ 跳过，稍后验证
            </Link>
            <Link href="/" className="text-muted-foreground hover:text-secondary-foreground transition-colors tracking-wider">
              ▸ 返回首页
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
