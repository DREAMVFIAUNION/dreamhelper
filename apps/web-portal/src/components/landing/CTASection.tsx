'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { MatrixRain } from './MatrixRain'
import { StarBorder } from './effects/StarBorder'
import { ShinyText } from './effects/ShinyText'

export function CTASection() {
  return (
    <section className="py-32 relative overflow-hidden border-t border-border">
      {/* 红色矩阵数字雨背景（慢速稀疏） */}
      <MatrixRain opacity={0.12} speed="slow" density={0.6} />

      {/* 背景光晕 */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                      w-[500px] h-[500px] rounded-full bg-primary/5 blur-[100px]" />

      <div className="relative z-10 text-center px-6">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-3xl md:text-5xl font-display font-bold"
        >
          <ShinyText text="体验三脑并行的力量" speed={3} color="hsl(var(--foreground))" />
        </motion.h2>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          viewport={{ once: true }}
          className="mt-4 text-muted-foreground font-mono"
        >
          三大脑协同思考，一个问题三重智慧
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          viewport={{ once: true }}
          className="mt-10"
        >
          <StarBorder speed="5s">
            <Link href="/login?mode=register" className="
              inline-block px-10 py-4 text-lg font-mono font-bold
              bg-primary text-primary-foreground
              shadow-[0_0_30px_hsl(var(--primary)/0.4)] hover:shadow-[0_0_50px_hsl(var(--primary)/0.5)]
              transition-all duration-300 hover:scale-105 rounded-md
            ">
              ▶ 免费开始使用
            </Link>
          </StarBorder>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          viewport={{ once: true }}
          className="mt-6 text-xs text-muted-foreground font-mono"
        >
          无需信用卡 · 永久免费版可用
        </motion.p>
      </div>
    </section>
  )
}
