'use client'

import { useState, useEffect, useCallback } from 'react'
import { Download, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const DISMISS_KEY = 'dreamhelp_pwa_dismissed'
const DISMISS_DAYS = 7

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [visible, setVisible] = useState(false)
  const [installing, setInstalling] = useState(false)

  useEffect(() => {
    // 检查是否已经安装或用户已关闭
    if (window.matchMedia('(display-mode: standalone)').matches) return
    const dismissed = localStorage.getItem(DISMISS_KEY)
    if (dismissed && Date.now() - Number(dismissed) < DISMISS_DAYS * 86400000) return

    const handler = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      setVisible(true)
    }

    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const handleInstall = useCallback(async () => {
    if (!deferredPrompt) return
    setInstalling(true)
    try {
      await deferredPrompt.prompt()
      const { outcome } = await deferredPrompt.userChoice
      if (outcome === 'accepted') {
        setVisible(false)
      }
    } finally {
      setInstalling(false)
      setDeferredPrompt(null)
    }
  }, [deferredPrompt])

  const handleDismiss = useCallback(() => {
    setVisible(false)
    setDeferredPrompt(null)
    localStorage.setItem(DISMISS_KEY, String(Date.now()))
  }, [])

  if (!visible) return null

  return (
    <div
      className={cn(
        'fixed bottom-20 left-1/2 -translate-x-1/2 z-50',
        'flex items-center gap-3 px-4 py-3 rounded-xl',
        'bg-card/95 backdrop-blur-md border border-border shadow-lg shadow-black/20',
        'animate-in slide-in-from-bottom-4 fade-in duration-300',
        'max-w-sm w-[calc(100%-2rem)]',
      )}
    >
      <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
        <Download size={18} className="text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">安装梦帮小助</p>
        <p className="text-[11px] text-muted-foreground">添加到桌面，获得原生体验</p>
      </div>
      <button
        onClick={handleInstall}
        disabled={installing}
        className={cn(
          'flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium',
          'bg-primary text-primary-foreground hover:bg-primary/90',
          'transition-colors disabled:opacity-50',
        )}
      >
        {installing ? '安装中...' : '安装'}
      </button>
      <button
        onClick={handleDismiss}
        className="flex-shrink-0 p-1 rounded-md text-muted-foreground hover:text-foreground transition-colors"
        aria-label="关闭"
      >
        <X size={14} />
      </button>
    </div>
  )
}
