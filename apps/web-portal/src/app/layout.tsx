import type { Metadata, Viewport } from 'next'
import { AuthProvider } from '@/lib/auth/AuthProvider'
import { PWAProvider } from '@/components/pwa/PWAProvider'
import 'katex/dist/katex.min.css'
import './globals.css'

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  viewportFit: 'cover',
  themeColor: '#ef4444',
}

export const metadata: Metadata = {
  title: 'DREAMVFIA · 梦帮小助 AI Assistant',
  description: '梦帮小助 v3.0 企业智能版 — DREAMVFIA AI Assistant',
  manifest: '/manifest.json',
  icons: {
    icon: '/favicon.ico',
    apple: '/logo/avatar-192.png',
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: '梦帮小助',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased">
        <AuthProvider>{children}</AuthProvider>
        <PWAProvider />
      </body>
    </html>
  )
}
