'use client'

import { motion } from 'framer-motion'
import { Brain, GitMerge, Database, Bot, Zap, Shield } from 'lucide-react'
import { SpotlightCard } from './effects/SpotlightCard'
import { ShinyText } from './effects/ShinyText'
import { StaggerGrid } from './effects/StaggerGrid'

const FEATURES = [
  {
    icon: Brain, title: '三脑并行', tag: 'TRIPLE_BRAIN',
    desc: '左脑(MiniMax)逻辑推理 + 右脑(Qwen-3)创意发散 + 脑干(GLM-4.7)质量监督，三路并行零额外延迟',
    highlights: ['三路并行', '零额外延迟', '质量监督'],
  },
  {
    icon: GitMerge, title: '双脑融合', tag: 'FUSION',
    desc: '自适应权重动态调优，融合缓存加速，EMA 追踪最优策略，每次对话都是三位专家协同',
    highlights: ['自适应权重', '融合缓存', 'EMA 追踪'],
  },
  {
    icon: Database, title: '智能RAG', tag: 'RAG',
    desc: '四种智能分块(文本/Markdown/代码/FAQ) + 查询改写多路召回，让知识真正被理解',
    highlights: ['智能分块', '查询改写', '多路召回'],
  },
  {
    icon: Bot, title: '多智能体', tag: 'AGENTS',
    desc: '编程/写作/分析/工具四大专业Agent，关键词+LLM双路路由，自动匹配最佳专家',
    highlights: ['四大专家', '双路路由', '自动匹配'],
  },
  {
    icon: Zap, title: '100+ 技能', tag: 'SKILLS',
    desc: '零 API 依赖的核心技能系统，覆盖日常、办公、文档、图像、音视频、编程、娱乐',
    highlights: ['零 API 依赖', '8 大类别', '离线可用'],
  },
  {
    icon: Shield, title: '企业级安全', tag: 'SECURITY',
    desc: 'AES-256-GCM 字段级加密，RBAC 权限控制，全操作审计日志，PIPL 合规',
    highlights: ['数据加密', 'RBAC 权限', '审计日志'],
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 relative">
      <div className="max-w-7xl mx-auto px-6">
        {/* 标题 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">CORE CAPABILITIES</p>
          <h2 className="text-3xl md:text-4xl font-display font-bold text-foreground">
            <ShinyText text="核心能力" speed={4} color="hsl(var(--foreground))" />
          </h2>
          <div className="mt-4 mx-auto w-20 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
        </motion.div>

        {/* 功能卡片网格 */}
        <StaggerGrid
          itemSelector="[data-stagger-item]"
          cols={3}
          rows={2}
          from="center"
          baseDelay={100}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {FEATURES.map(({ icon: Icon, title, tag, desc, highlights }) => (
            <div
              key={tag}
              data-stagger-item
            >
            <SpotlightCard className="
                group relative p-6
                bg-card/80 border border-border
                hover:border-primary/40 hover:bg-secondary/80 hover:shadow-[0_0_20px_hsl(var(--primary)/0.06)]
                transition-all duration-300
                [clip-path:polygon(8px_0%,100%_0%,100%_calc(100%-8px),calc(100%-8px)_100%,0%_100%,0%_8px)]
              ">
              {/* 切角装饰 */}
              <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-primary/40 group-hover:border-primary transition-colors" />
              <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-primary/40 group-hover:border-primary transition-colors" />

              {/* 标签 */}
              <span className="text-[10px] font-mono text-primary/60 tracking-[0.2em]">{tag}</span>

              {/* 图标 + 标题 */}
              <div className="flex items-center gap-3 mt-3 mb-4">
                <div className="w-10 h-10 flex items-center justify-center bg-primary/10 border border-primary/20
                                group-hover:bg-primary/20 group-hover:border-primary/40 transition-all
                                [clip-path:polygon(4px_0%,100%_0%,100%_calc(100%-4px),calc(100%-4px)_100%,0%_100%,0%_4px)]">
                  <Icon size={20} className="text-primary" />
                </div>
                <h3 className="text-lg font-bold text-foreground">{title}</h3>
              </div>

              {/* 描述 */}
              <p className="text-sm text-muted-foreground leading-relaxed mb-4">{desc}</p>

              {/* 高亮标签 */}
              <div className="flex flex-wrap gap-2">
                {highlights.map((h) => (
                  <span key={h} className="text-[11px] font-mono px-2 py-0.5
                    bg-secondary border border-border text-muted-foreground
                    group-hover:border-primary/30 group-hover:text-primary/80 transition-colors">
                    {h}
                  </span>
                ))}
              </div>
            </SpotlightCard>
            </div>
          ))}
        </StaggerGrid>
      </div>
    </section>
  )
}
