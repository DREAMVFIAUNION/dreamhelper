import type { Metadata } from 'next'
import { LandingNav } from '@/components/landing/LandingNav'
import { LandingFooter } from '@/components/landing/LandingFooter'
import { ScrollProgress } from '@/components/landing/ScrollProgress'
import { MatrixRainBackground } from '@/components/landing/MatrixRainBackground'

export const metadata: Metadata = {
  title: 'DREAMVFIA · 梦帮小助 — 你的超级 AI 助手',
  description: '100+ 核心技能，零 API 依赖，企业级安全。智能对话、知识库 RAG、多智能体协作，一站式 AI 工作平台。',
  keywords: ['AI助手', '智能对话', '梦帮小助', 'DREAMVFIA', 'AI工具', '知识库', 'RAG'],
  openGraph: {
    title: 'DREAMVFIA · 梦帮小助',
    description: '你的超级 AI 助手，已觉醒',
    images: ['/og-image.png'],
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'DREAMVFIA · 梦帮小助',
    description: '你的超级 AI 助手，已觉醒',
    images: ['/og-image.png'],
  },
}

export default function LandingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground font-body">
      {/* 全局网格背景 */}
      <div className="fixed inset-0 bg-grid-cyber opacity-20 pointer-events-none" />
      {/* 全局微弱矩阵数字雨 */}
      <MatrixRainBackground />
      {/* 全局扫描线 */}
      <div className="fixed inset-0 bg-scanline opacity-10 pointer-events-none" />

      {/* 滚动进度条（顶部红色细线） */}
      <ScrollProgress />

      {/* 导航栏 */}
      <LandingNav />

      {/* 主内容 */}
      <main>{children}</main>

      {/* 页脚 */}
      <LandingFooter />
    </div>
  )
}
