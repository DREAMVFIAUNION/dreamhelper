'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { Menu, X, LogIn, UserPlus, LayoutDashboard } from 'lucide-react'
import { useAuth } from '@/lib/auth/AuthProvider'

const NAV_LINKS = [
  { href: '/features', label: '功能' },
  { href: '/pricing',  label: '定价' },
  { href: '/about',    label: '关于' },
]

export function LandingNav() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, loading } = useAuth()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header className={cn(
      'fixed top-0 left-0 right-0 z-50 h-16 transition-all duration-300',
      scrolled
        ? 'bg-card/90 backdrop-blur-xl border-b border-border shadow-md'
        : 'bg-transparent',
      'after:absolute after:bottom-0 after:left-0 after:right-0',
      'after:h-px after:bg-gradient-to-r after:from-transparent after:via-primary after:to-transparent',
      !scrolled && 'after:opacity-30',
    )}>
      <div className="max-w-7xl mx-auto flex items-center justify-between h-full px-6">
        {/* 品牌 */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative w-10 h-10 drop-shadow-[0_0_8px_#FE000080] group-hover:drop-shadow-[0_0_16px_#FE000090] transition-all">
            <Image src="/logo/logo.png" alt="DREAMVFIA" fill sizes="40px" className="object-contain" priority />
          </div>
          <span className="font-display text-base font-black tracking-[0.2em] text-primary animate-flicker
                           drop-shadow-[0_0_6px_hsl(var(--primary)/0.5)]">
            DREAMVFIA
          </span>
        </Link>

        {/* 桌面导航 */}
        <nav className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map(({ href, label }) => (
            <Link key={href} href={href} className="
              text-sm font-mono text-muted-foreground hover:text-primary
              transition-colors duration-200 tracking-wider
              hover:drop-shadow-[0_0_4px_hsl(var(--primary)/0.4)]
            ">
              {label}
            </Link>
          ))}
        </nav>

        {/* 右侧操作区 — 登录态感知 */}
        <div className="hidden md:flex items-center gap-3">
          {!loading && user ? (
            <>
              <Link href="/overview" className="
                flex items-center gap-2 px-4 py-2 text-sm font-mono font-bold
                bg-primary text-primary-foreground
                shadow-[0_0_15px_hsl(var(--primary)/0.2)] hover:shadow-[0_0_25px_hsl(var(--primary)/0.3)]
                transition-all duration-200 rounded-md
              ">
                <LayoutDashboard size={14} />
                进入工作台
              </Link>
              {user.avatarUrl ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={user.avatarUrl} alt="" className="w-8 h-8 rounded border border-border" />
              ) : (
                <div className="w-8 h-8 rounded bg-primary/20 border border-primary/40 flex items-center justify-center text-primary text-xs font-bold">
                  {(user.displayName ?? user.username)?.[0]?.toUpperCase() ?? 'U'}
                </div>
              )}
            </>
          ) : (
            <>
              <Link href="/login" className="
                flex items-center gap-1.5 px-4 py-2 text-sm font-mono text-muted-foreground
                hover:text-primary transition-colors
              ">
                <LogIn size={14} />
                登录
              </Link>
              <Link href="/register" className="
                flex items-center gap-1.5 px-5 py-2 text-sm font-mono font-bold
                bg-primary text-primary-foreground
                shadow-[0_0_15px_hsl(var(--primary)/0.2)] hover:shadow-[0_0_25px_hsl(var(--primary)/0.3)]
                transition-all duration-200 rounded-md
              ">
                <UserPlus size={14} />
                免费开始 →
              </Link>
            </>
          )}
        </div>

        {/* 移动端菜单按钮 */}
        <button className="md:hidden text-muted-foreground" onClick={() => setMobileOpen(!mobileOpen)} aria-label={mobileOpen ? '关闭菜单' : '打开菜单'} aria-expanded={mobileOpen}>
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* 移动端菜单 */}
      {mobileOpen && (
        <div className="md:hidden bg-card/95 backdrop-blur-xl border-t border-border">
          <nav aria-label="移动端导航" className="flex flex-col px-6 py-4 gap-4">
            {NAV_LINKS.map(({ href, label }) => (
              <Link key={href} href={href} className="text-sm font-mono text-muted-foreground py-2 border-b border-border">
                {label}
              </Link>
            ))}
            {user ? (
              <Link href="/overview" className="
                mt-2 px-5 py-3 text-sm font-mono font-bold text-center
                bg-primary text-primary-foreground shadow-[0_0_15px_hsl(var(--primary)/0.2)] rounded-md
              ">
                进入工作台 →
              </Link>
            ) : (
              <>
                <Link href="/login" className="text-sm font-mono text-muted-foreground py-2 border-b border-border">
                  登录
                </Link>
                <Link href="/register" className="
                  mt-2 px-5 py-3 text-sm font-mono font-bold text-center
                  bg-primary text-primary-foreground shadow-[0_0_15px_hsl(var(--primary)/0.2)] rounded-md
                ">
                  免费开始 →
                </Link>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
