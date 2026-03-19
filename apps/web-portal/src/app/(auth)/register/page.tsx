'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState, useCallback, useEffect, type FormEvent } from 'react'
import { useAuth } from '@/lib/auth/AuthProvider'
import { RefreshCw } from 'lucide-react'

interface CaptchaData {
  captchaId: string
  svg: string
}

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

export default function RegisterPage() {
  const router = useRouter()
  const { register } = useAuth()

  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [captchaAnswer, setCaptchaAnswer] = useState('')
  const [captcha, setCaptcha] = useState<CaptchaData | null>(null)
  const [captchaVerifyToken, setCaptchaVerifyToken] = useState('')
  const [captchaVerified, setCaptchaVerified] = useState(false)
  const [errors, setErrors] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)

  const loadCaptcha = useCallback(async () => {
    setCaptchaAnswer('')
    setCaptchaVerifyToken('')
    setCaptchaVerified(false)
    try {
      const res = await fetch('/api/auth/captcha')
      const data = (await res.json()) as CaptchaData
      setCaptcha(data)
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    void loadCaptcha()
  }, [loadCaptcha])

  async function verifyCaptcha() {
    if (!captcha || !captchaAnswer) return
    try {
      const res = await fetch('/api/auth/captcha', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ captchaId: captcha.captchaId, answer: captchaAnswer }),
      })
      const data = (await res.json()) as { valid: boolean; verifyToken?: string; error?: string }
      if (data.valid && data.verifyToken) {
        setCaptchaVerifyToken(data.verifyToken)
        setCaptchaVerified(true)
      } else {
        setErrors([data.error ?? '验证码错误'])
        void loadCaptcha()
      }
    } catch {
      setErrors(['验证码校验失败'])
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErrors([])

    const errs: string[] = []
    if (!email) errs.push('请填写邮箱')
    if (!username) errs.push('请填写用户名')
    if (password.length < 8) errs.push('密码至少 8 位')
    if (!/[A-Z]/.test(password)) errs.push('密码需包含大写字母')
    if (!/[a-z]/.test(password)) errs.push('密码需包含小写字母')
    if (!/\d/.test(password)) errs.push('密码需包含数字')
    if (password !== confirmPassword) errs.push('两次密码不一致')
    if (!captchaVerified) errs.push('请先完成验证码校验')

    if (errs.length > 0) {
      setErrors(errs)
      return
    }

    setSubmitting(true)
    try {
      const result = await register({ email, username, password, captchaVerifyToken })
      if (result.success) {
        router.push('/overview')
      } else {
        setErrors(result.errors ?? ['注册失败'])
        void loadCaptcha()
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
                CREATE ACCOUNT
              </h1>
              <p className="font-mono text-[10px] text-muted-foreground tracking-widest mt-1">
                注册成为 DREAMVFIA 用户
              </p>
            </div>
          </div>

          {/* 错误提示 */}
          {errors.length > 0 && (
            <div className="mb-4 p-3 bg-destructive/10 border border-destructive/30 text-destructive text-xs font-mono rounded-md">
              {errors.map((err, i) => (
                <div key={i}>⚠ {err}</div>
              ))}
            </div>
          )}

          <form className="space-y-3" onSubmit={handleSubmit}>
            {/* 邮箱 */}
            <div className="space-y-1">
              <label className="block text-[10px] font-mono text-muted-foreground tracking-widest">电子邮箱 / EMAIL</label>
              <input type="email" placeholder="user@example.com" value={email} onChange={(e) => setEmail(e.target.value)} disabled={submitting} className={inputCls} />
            </div>

            {/* 用户名 */}
            <div className="space-y-1">
              <label className="block text-[10px] font-mono text-muted-foreground tracking-widest">用户名 / USERNAME</label>
              <input type="text" placeholder="2-20 位，字母/数字/下划线/中文" value={username} onChange={(e) => setUsername(e.target.value)} disabled={submitting} className={inputCls} />
            </div>

            {/* 密码 */}
            <div className="space-y-1">
              <label className="block text-[10px] font-mono text-muted-foreground tracking-widest">设置密码 / PASSWORD</label>
              <input type="password" placeholder="至少 8 位，含大小写+数字" value={password} onChange={(e) => setPassword(e.target.value)} disabled={submitting} className={inputCls} />
              <PasswordStrength password={password} />
            </div>

            {/* 确认密码 */}
            <div className="space-y-1">
              <label className="block text-[10px] font-mono text-muted-foreground tracking-widest">确认密码 / CONFIRM</label>
              <input type="password" placeholder="再次输入密码" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} disabled={submitting} className={inputCls} />
              {confirmPassword && password !== confirmPassword && (
                <p className="text-[10px] font-mono text-destructive mt-0.5">密码不一致</p>
              )}
            </div>

            {/* 验证码 */}
            <div className="space-y-1">
              <label className="block text-[10px] font-mono text-muted-foreground tracking-widest">安全验证 / CAPTCHA</label>
              <div className="flex items-center gap-2">
                {captcha?.svg ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img src={captcha.svg} alt="验证码" className="h-10 border border-border rounded-md" />
                ) : (
                  <div className="h-10 w-[150px] bg-secondary border border-border rounded-md flex items-center justify-center text-[10px] text-muted-foreground font-mono">
                    加载中...
                  </div>
                )}
                <button type="button" onClick={() => void loadCaptcha()} className="p-2 text-muted-foreground hover:text-primary transition-colors" title="刷新验证码">
                  <RefreshCw size={14} />
                </button>
              </div>
              <div className="flex gap-2 mt-1">
                <input
                  type="text"
                  placeholder="输入验证码"
                  maxLength={4}
                  value={captchaAnswer}
                  onChange={(e) => setCaptchaAnswer(e.target.value)}
                  disabled={submitting || captchaVerified}
                  className={inputCls + ' flex-1'}
                />
                <button
                  type="button"
                  onClick={() => void verifyCaptcha()}
                  disabled={!captchaAnswer || captchaVerified || submitting}
                  className="px-3 py-2 bg-secondary border border-border text-xs font-mono text-secondary-foreground hover:border-primary/50 transition-colors rounded-md disabled:opacity-50"
                >
                  {captchaVerified ? '✓ 已验证' : '校验'}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting || !captchaVerified}
              className="w-full mt-4 py-3 bg-primary text-primary-foreground font-mono font-bold text-sm shadow-[0_0_12px_hsl(var(--primary)/0.3)] hover:bg-primary/90 hover:shadow-[0_0_16px_hsl(var(--primary)/0.4)] active:scale-[0.98] transition-all duration-150 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? '▶ 创建中...' : '▶ 创建账号'}
            </button>
          </form>

          <div className="mt-6 flex items-center justify-between text-[10px] font-mono">
            <Link href="/login" className="text-muted-foreground hover:text-primary transition-colors tracking-wider">
              ▸ 已有账号？登录
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
