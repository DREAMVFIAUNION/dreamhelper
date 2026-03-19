'use client'

import Link from 'next/link'
import { useAuth } from '@/lib/auth/AuthProvider'

export function EmailVerifyBanner() {
  const { user } = useAuth()

  if (!user || user.emailVerified) return null

  return (
    <div className="bg-yellow-500/10 border-b border-yellow-500/30 px-4 py-2 flex items-center justify-between gap-4">
      <div className="flex items-center gap-2 text-xs font-mono text-yellow-500">
        <span>📧</span>
        <span>邮箱尚未验证，部分功能可能受限</span>
      </div>
      <Link
        href="/verify"
        className="px-3 py-1 text-[10px] font-mono font-bold bg-yellow-500/20 text-yellow-500 border border-yellow-500/30 hover:bg-yellow-500/30 transition-colors rounded-md whitespace-nowrap"
      >
        立即验证
      </Link>
    </div>
  )
}
