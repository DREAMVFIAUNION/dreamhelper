'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { ChevronDown } from 'lucide-react'
import { HeroVideoCarousel } from './HeroVideoCarousel'
import { HeroBrandText } from './effects/HeroBrandText'
import { DecryptedText } from './effects/DecryptedText'
import { StarBorder } from './effects/StarBorder'
import { HeroBrainLogo } from './effects/HeroBrainLogo'

export function HeroSection() {
  return (
    <section className="relative h-screen flex items-center justify-center overflow-hidden">
      {/* 视频轮播背景 */}
      <HeroVideoCarousel />

      {/* 内容 */}
      <div className="relative z-10 text-center px-6">
        {/* LOGO × 机械大脑融合动画 */}
        <div className="mx-auto w-[22rem] h-[22rem] md:w-96 md:h-96 mb-4 relative">
          <HeroBrainLogo className="w-full h-full" />
        </div>

        {/* 品牌名 — SVG 机械解构动画 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="max-w-2xl mx-auto"
        >
          <HeroBrandText />
        </motion.div>

        {/* 副标题 */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="mt-4 font-mono text-lg md:text-xl text-muted-foreground tracking-widest"
        >
          ─── <DecryptedText text="三脑并行 · 思考不设限" speed={40} className="text-muted-foreground" encryptedClassName="text-primary/50" /> ───
        </motion.p>

        {/* 核心理念 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.6 }}
          className="mt-6 flex items-center justify-center gap-4 text-sm font-mono text-muted-foreground"
        >
          <span className="flex items-center gap-1.5">
            <span className="w-1 h-1 bg-primary rounded-full" />
            左脑逻辑
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1 h-1 bg-primary rounded-full" />
            右脑创意
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1 h-1 bg-primary rounded-full" />
            脑干监督
          </span>
        </motion.div>

        {/* CTA 按钮 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0, duration: 0.6 }}
          className="mt-10 flex items-center justify-center gap-4"
        >
          <StarBorder speed="5s">
            <Link href="/login?mode=register" className="
              block px-8 py-3.5 text-base font-mono font-bold
              bg-primary text-primary-foreground
              shadow-[0_0_20px_hsl(var(--primary)/0.3)] hover:shadow-[0_0_30px_hsl(var(--primary)/0.5)]
              transition-all duration-300 hover:scale-105 rounded-md
            ">
              ▶ 免费体验
            </Link>
          </StarBorder>
          <a href="#features" className="
            px-8 py-3.5 text-base font-mono
            border border-border text-muted-foreground
            hover:border-primary hover:text-primary hover:shadow-[0_0_15px_hsl(var(--primary)/0.2)]
            transition-all duration-300 rounded-md
          ">
            了解更多 ↓
          </a>
        </motion.div>
      </div>

      {/* 底部滚动提示 */}
      <motion.div
        animate={{ y: [0, 8, 0] }}
        transition={{ repeat: Infinity, duration: 2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 text-muted-foreground"
      >
        <ChevronDown size={24} className="opacity-40" />
      </motion.div>

      {/* 底部红色渐变分割线 */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
    </section>
  )
}
