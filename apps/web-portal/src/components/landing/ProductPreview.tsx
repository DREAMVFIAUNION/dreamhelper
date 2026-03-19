'use client'

import { useState } from 'react'
import Image from 'next/image'
import { motion, AnimatePresence } from 'framer-motion'
import { ShinyText } from './effects/ShinyText'
import { ScrollParallax } from './effects/ScrollParallax'

const TABS = [
  { key: 'analysis',  label: '深度分析',  img: '/screenshots/chat-analysis.png',  desc: '三脑并行对比 React/Vue/Svelte 三大框架' },
  { key: 'coding',    label: '代码生成',  img: '/screenshots/chat-coding.png',    desc: '编程Agent生成带重试机制的Python装饰器' },
  { key: 'reasoning', label: '逻辑推理',  img: '/screenshots/chat-reasoning.png', desc: '脑干监督下的P-NP问题深度推理' },
]

export function ProductPreview() {
  const [active, setActive] = useState('analysis')
  const current = TABS.find(t => t.key === active)!

  return (
    <section className="py-24 border-t border-border">
      <div className="max-w-6xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">TRIPLE-BRAIN IN ACTION</p>
          <h2 className="text-3xl md:text-4xl font-display font-bold">
            <ShinyText text="三脑实战演示" speed={4} color="hsl(var(--foreground))" />
          </h2>
          <p className="mt-3 text-sm text-muted-foreground font-mono">左脑推理 · 右脑创意 · 脑干监督 — 真实对话截图</p>
        </motion.div>

        {/* 浏览器窗口模拟 */}
        <ScrollParallax offsetY={20} scaleRange={[0.97, 1.01]}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative border border-primary/30 shadow-[0_0_30px_hsl(var(--primary)/0.08)] rounded-sm overflow-hidden"
        >
          {/* 浏览器标题栏 */}
          <div className="flex items-center gap-2 px-4 py-2.5 bg-card border-b border-border">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-primary/60" />
              <div className="w-3 h-3 rounded-full bg-muted-foreground/20" />
              <div className="w-3 h-3 rounded-full bg-muted-foreground/20" />
            </div>
            <div className="flex-1 mx-4 px-3 py-1 bg-secondary rounded-sm text-xs font-mono text-muted-foreground text-center">
              app.dreamvfia.com
            </div>
          </div>

          {/* 截图区域 */}
          <div className="relative aspect-[16/9] bg-background">
            <AnimatePresence mode="wait">
              <motion.div
                key={active}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0"
              >
                <Image
                  src={current.img}
                  alt={current.desc}
                  fill
                  className="object-cover object-top"
                  sizes="(max-width: 768px) 100vw, 1152px"
                />
              </motion.div>
            </AnimatePresence>
          </div>

          {/* 标签切换 */}
          <div className="flex items-center justify-center gap-4 py-3 bg-card border-t border-border">
            {TABS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setActive(key)}
                className={`text-xs font-mono px-3 py-1 transition-all ${
                  active === key
                    ? 'text-primary border-b border-primary'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {active === key ? '●' : '○'} {label}
              </button>
            ))}
          </div>
        </motion.div>
        </ScrollParallax>
      </div>
    </section>
  )
}
