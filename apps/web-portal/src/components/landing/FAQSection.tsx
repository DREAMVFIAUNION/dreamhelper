'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ShinyText } from './effects/ShinyText'

const FAQS = [
  { q: '什么是三脑并行？', a: '三脑并行是 DREAMVFIA 的核心架构：左脑(MiniMax M2.5)负责逻辑推理，右脑(Qwen-3-235B)负责创意发散，脑干(GLM-4.7)负责质量监督。三路使用 asyncio.gather 并行执行，零额外延迟，延迟降低 33%。' },
  { q: '支持哪些 AI 模型？', a: '内置三大脑：MiniMax M2.5（左脑逻辑）、Qwen-3-235B（右脑创意）、GLM-4.7（脑干推理监督）。融合权重基于 EMA 动态自适应调优，架构可扩展接入更多模型。' },
  { q: '我的数据安全吗？', a: '所有敏感数据使用 AES-256-GCM 加密存储，传输使用 TLS 1.3，符合中国《个人信息保护法》要求。全操作审计日志，RBAC 权限控制。' },
  { q: '100 个技能需要联网吗？', a: '核心技能系统完全零 API 依赖，离线可用。部分高级功能（如三脑对话、知识库 RAG）需要网络连接。' },
  { q: '与普通 ChatGPT 有何不同？', a: 'ChatGPT 是单模型单次响应；DREAMVFIA 是三模型并行思考 + 自适应融合 + 脑干质量监督，相当于三位专家同时分析后给出最优答案，回答质量和稳定性显著提升。' },
  { q: '如何付款？', a: '支持支付宝、微信支付、银联三大支付渠道，H5/扫码/PC 网页多种方式。提供免费版每日 5000 Token 额度。' },
]

export function FAQSection() {
  const [open, setOpen] = useState<number | null>(null)

  return (
    <section className="py-24 border-t border-border">
      <div className="max-w-3xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">FAQ</p>
          <h2 className="text-3xl md:text-4xl font-display font-bold">
            <ShinyText text="常见问题" speed={4} color="hsl(var(--foreground))" />
          </h2>
        </motion.div>

        <div className="space-y-2">
          {FAQS.map(({ q, a }, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ delay: i * 0.05 }}
              viewport={{ once: true }}
              className="border border-border bg-card/80
                         hover:border-primary/20 transition-colors
                         [clip-path:polygon(4px_0%,100%_0%,100%_calc(100%-4px),calc(100%-4px)_100%,0%_100%,0%_4px)]"
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between px-5 py-4 text-left"
              >
                <span className="text-sm font-medium text-foreground">{q}</span>
                <ChevronDown size={16} className={cn(
                  'text-muted-foreground transition-transform duration-200',
                  open === i && 'rotate-180 text-primary'
                )} />
              </button>
              {open === i && (
                <div className="px-5 pb-4 text-sm text-muted-foreground leading-relaxed border-t border-border pt-3">
                  {a}
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
