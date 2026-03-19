'use client'

import { motion } from 'framer-motion'
import { CountUp } from './effects/CountUp'
import { ScrollParallax } from './effects/ScrollParallax'

const STATS = [
  { value: 3,      suffix: '',   label: '并行大脑' },
  { value: 100,    suffix: '+',  label: '核心技能' },
  { value: 33,     suffix: '%',  label: '延迟降低' },
  { value: 99.9,   suffix: '%',  label: '系统可用率' },
]

function AnimatedStat({ value, suffix }: { value: number; suffix: string }) {
  return (
    <span className="font-display text-4xl md:text-5xl font-black text-primary
                      drop-shadow-[0_0_10px_hsl(var(--primary)/0.4)]">
      <CountUp to={value} duration={2} className="" />{suffix}
    </span>
  )
}

export function StatsSection() {
  return (
    <section className="py-20 border-t border-b border-border bg-card/50">
      <ScrollParallax offsetY={15}>
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {STATS.map(({ value, suffix, label }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.15 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <AnimatedStat value={value} suffix={suffix} />
              <p className="mt-2 text-sm font-mono text-muted-foreground tracking-wider">{label}</p>
            </motion.div>
          ))}
        </div>
      </div>
      </ScrollParallax>
    </section>
  )
}
