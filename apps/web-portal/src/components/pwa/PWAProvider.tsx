'use client'

import { useEffect } from 'react'
import { registerServiceWorker } from '@/lib/pwa/register-sw'
import { InstallPrompt } from './InstallPrompt'

export function PWAProvider() {
  useEffect(() => {
    registerServiceWorker()
  }, [])

  return <InstallPrompt />
}
