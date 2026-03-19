'use client'

import { motion } from 'framer-motion'
import Image from 'next/image'

export default function AboutPage() {
  return (
    <div className="pt-24 pb-20">
      <div className="max-w-4xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">ABOUT US</p>
          <h1 className="text-3xl md:text-5xl font-display font-bold">关于 DREAMVFIA</h1>
          <div className="mt-4 mx-auto w-20 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="space-y-8 text-muted-foreground leading-relaxed"
        >
          <div className="flex items-start gap-6">
            <div className="relative w-16 h-16 flex-shrink-0">
              <Image src="/logo/logo.png" alt="DREAMVFIA" fill sizes="64px" className="object-contain" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground mb-3">梦帮 · DREAMVFIA</h2>
              <p className="text-sm">
                DREAMVFIA 致力于打造下一代 AI 智能助手平台。我们相信 AI 应该是每个人的超级助手 ——
                不让你思考、不让你等待、不让你重复。
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              { title: '使命', desc: '让 AI 成为每个人和每个团队的超级助手，降低智能工具的使用门槛。' },
              { title: '愿景', desc: '构建一个开放、安全、高效的 AI 工作平台，连接人与智能。' },
              { title: '技术', desc: '基于 MiniMax、OpenAI 等多模型架构，100+ 零依赖技能，企业级安全。' },
              { title: '团队', desc: '由一群热爱 AI 和产品的工程师组成，追求极致的用户体验。' },
            ].map(({ title, desc }) => (
              <div key={title} className="p-5 bg-card border border-border rounded-md">
                <h3 className="text-sm font-mono text-primary tracking-wider mb-2">{title}</h3>
                <p className="text-sm text-muted-foreground">{desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
