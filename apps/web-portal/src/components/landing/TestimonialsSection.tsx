'use client'

import { motion } from 'framer-motion'
import { ShinyText } from './effects/ShinyText'

const TESTIMONIALS = [
  {
    quote: '三脑并行的回答质量明显高于单模型，尤其是复杂技术问题的分析深度，能同时给出逻辑严谨和创意灵活的双重视角。',
    name: '张工程师', role: '某科技公司 · 后端开发',
  },
  {
    quote: '代码生成Agent直接给出可运行的方案，还自带重试机制和错误处理，专业水准。100个内置技能也太方便了。',
    name: '李设计师', role: '自由职业 · 全栈开发',
  },
  {
    quote: '脑干监督机制让我很放心，回答不会跑偏，质量稳定。企业级加密和审计日志也很完善，团队放心使用。',
    name: '王 CTO', role: '某企业 · 技术负责人',
  },
]

export function TestimonialsSection() {
  return (
    <section className="py-24 border-t border-border">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">TESTIMONIALS</p>
          <h2 className="text-3xl md:text-4xl font-display font-bold">
            <ShinyText text="用户评价" speed={4} color="hsl(var(--foreground))" />
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TESTIMONIALS.map(({ quote, name, role }, i) => (
            <motion.div
              key={name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.15 }}
              viewport={{ once: true }}
              className="
                p-6 bg-card/80 border border-border
                hover:border-primary/30 hover:shadow-[0_0_15px_hsl(var(--primary)/0.04)] transition-all
                [clip-path:polygon(8px_0%,100%_0%,100%_calc(100%-8px),calc(100%-8px)_100%,0%_100%,0%_8px)]
              "
            >
              <div className="text-primary text-2xl mb-4 font-display">&ldquo;</div>
              <p className="text-sm text-muted-foreground leading-relaxed mb-6">{quote}</p>
              <div className="border-t border-border pt-4">
                <p className="text-sm font-bold text-foreground">{name}</p>
                <p className="text-xs text-muted-foreground font-mono">{role}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
