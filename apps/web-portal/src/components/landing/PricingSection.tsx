'use client'

import { useCallback, useRef } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Check } from 'lucide-react'
import { ElectricBorder } from './effects/ElectricBorder'
import { ShinyText } from './effects/ShinyText'

function useTilt3D() {
  const ref = useRef<HTMLDivElement>(null)
  const onMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width - 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5
    ref.current.style.transform = `perspective(800px) rotateY(${x * 8}deg) rotateX(${-y * 8}deg) scale3d(1.02, 1.02, 1.02)`
  }, [])
  const onLeave = useCallback(() => {
    if (!ref.current) return
    ref.current.style.transform = 'perspective(800px) rotateY(0deg) rotateX(0deg) scale3d(1, 1, 1)'
  }, [])
  return { ref, onMove, onLeave }
}

const PLANS = [
  {
    name: '免费版', price: '0', period: '/月', yearly: '',
    desc: '基础功能体验', featured: false,
    features: ['每日 5,000 Token', '基础对话', '3 个智能体', '社区支持'],
    cta: '开始使用', ctaHref: '/login?mode=register',
  },
  {
    name: '专业版', price: '29.9', period: '/月', yearly: '年付 ¥299 省 37%',
    desc: '专业级 AI 助手', featured: true,
    features: ['每月 50万 Token', '全部 100 技能', '10 个智能体', '知识库 500MB', '优先响应', '邮件支持'],
    cta: '立即升级 →', ctaHref: '/login?mode=register&plan=pro',
  },
  {
    name: '企业版', price: '99.9', period: '/月', yearly: '年付 ¥999 省 17%',
    desc: '企业级解决方案', featured: false,
    features: ['每月 200万 Token', '全部 100 技能', '无限智能体', '知识库 2GB', '团队协作', 'API 接入', '专属客服'],
    cta: '联系销售', ctaHref: '/contact',
  },
]

type Plan = typeof PLANS[number]

function PricingCard({ plan, index }: { plan: Plan; index: number }) {
  const { ref, onMove, onLeave } = useTilt3D()
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.15 }}
      viewport={{ once: true }}
    >
      <div
        ref={ref}
        onMouseMove={onMove}
        onMouseLeave={onLeave}
        className={`
          relative p-6
          bg-card/80 border
          transition-all duration-300 rounded-lg
          ${plan.featured
            ? 'border-primary/40 shadow-[0_0_30px_hsl(var(--primary)/0.08)] scale-105 z-10'
            : 'border-border hover:border-primary/30 hover:shadow-[0_0_15px_hsl(var(--primary)/0.04)]'}
        `}
        style={{ transformStyle: 'preserve-3d', willChange: 'transform' }}
      >
        {plan.featured && (
          <>
            <ElectricBorder speed={0.8} chaos={0.08} borderRadius={8} className="!absolute inset-0 pointer-events-none" />
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5
                            bg-primary text-primary-foreground text-[10px] font-mono font-bold tracking-wider rounded-sm z-10">
              推荐
            </div>
          </>
        )}

        <h3 className="text-lg font-bold text-foreground relative z-10">{plan.name}</h3>
        <p className="text-xs text-muted-foreground/90 mt-1">{plan.desc}</p>

        <div className="mt-6 mb-2">
          <span className="text-3xl font-display font-black text-primary">¥{plan.price}</span>
          <span className="text-sm text-muted-foreground">{plan.period}</span>
        </div>
        {plan.yearly && (
          <p className="text-xs text-emerald-400 font-mono">{plan.yearly}</p>
        )}

        <ul className="mt-6 space-y-3">
          {plan.features.map((f) => (
            <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
              <Check size={14} className="text-primary flex-shrink-0" />
              {f}
            </li>
          ))}
        </ul>

        <Link href={plan.ctaHref} className={`
          mt-8 block text-center py-3 text-sm font-mono font-bold
          transition-all duration-200
          [clip-path:polygon(4px_0%,100%_0%,100%_calc(100%-4px),calc(100%-4px)_100%,0%_100%,0%_4px)]
          ${plan.featured
            ? 'bg-primary text-primary-foreground shadow-[0_0_15px_hsl(var(--primary)/0.2)] hover:shadow-[0_0_25px_hsl(var(--primary)/0.3)]'
            : 'bg-secondary text-foreground border border-border hover:border-primary hover:text-primary'}
        `}>
          {plan.cta}
        </Link>
      </div>
    </motion.div>
  )
}

export function PricingSection() {
  return (
    <section id="pricing" className="py-24 border-t border-border">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">PRICING</p>
          <h2 className="text-3xl md:text-4xl font-display font-bold">
            <ShinyText text="选择方案" speed={4} color="hsl(var(--foreground))" />
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
          {PLANS.map((plan, i) => (
            <PricingCard key={plan.name} plan={plan} index={i} />
          ))}
        </div>
      </div>
    </section>
  )
}
