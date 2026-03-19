'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { MessageSquare, BookOpen, Brain, Database, Zap, Shield, ChevronRight, Mail } from 'lucide-react'

const GUIDES = [
  {
    icon: MessageSquare,
    title: '开始对话',
    desc: '注册账号后，进入对话页面即可与梦帮小助交流。支持文字、语音、图片多种输入方式。',
    href: '/chat',
  },
  {
    icon: Database,
    title: '知识库',
    desc: '上传文档（PDF、Markdown、TXT），系统自动分块索引。对话中 AI 将自动检索相关知识回答问题。',
    href: '/knowledge',
  },
  {
    icon: Brain,
    title: '三脑并行',
    desc: '左脑（MiniMax）负责逻辑推理，右脑（Qwen-3）负责创意发散，脑干（GLM-4.7）负责质量监督。三路并行零额外延迟。',
    href: '/features',
  },
  {
    icon: Zap,
    title: '智能体 & 技能',
    desc: '系统内置编程、写作、分析、工具四大专业 Agent，100+ 零依赖技能覆盖日常办公各场景。',
    href: '/features',
  },
  {
    icon: Shield,
    title: '账户安全',
    desc: 'AES-256-GCM 字段级加密，RBAC 权限控制。在「设置」中可修改密码、管理 API Key、查看登录记录。',
    href: '/settings',
  },
  {
    icon: BookOpen,
    title: '开发者接入',
    desc: '提供 REST API 和多渠道 Webhook 接入（微信公众号、企业微信、Telegram），详见开发者文档。',
    href: '/docs',
  },
]

const FAQ = [
  {
    q: '如何修改密码？',
    a: '登录后进入「设置 → 安全」页面，点击「修改密码」即可。',
  },
  {
    q: '对话消息会被保存吗？',
    a: '是的，对话历史保存在您的账户中，您可以随时在侧边栏查看历史会话。所有数据均使用 AES-256-GCM 加密存储。',
  },
  {
    q: '免费版有什么限制？',
    a: '免费版每日 5,000 Token，支持基础对话和 3 个智能体。升级专业版可获得每月 50 万 Token 和全部 100 技能。',
  },
  {
    q: '支持哪些文件格式上传到知识库？',
    a: '目前支持 PDF、Markdown、TXT、DOCX 格式。上传后系统自动进行智能分块和向量索引。',
  },
  {
    q: '三脑模式可以关闭吗？',
    a: '三脑并行是默认启用的核心特性，系统会根据问题复杂度自动选择单脑或多脑模式，无需手动切换。',
  },
  {
    q: '如何联系客服？',
    a: '您可以通过邮箱 support@dreamvfia.com 联系我们，或加入 Discord 社区获得即时帮助。',
  },
]

export default function HelpPage() {
  return (
    <div className="pt-24 pb-20">
      <div className="max-w-5xl mx-auto px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">HELP CENTER</p>
          <h1 className="text-3xl md:text-5xl font-display font-bold">帮助中心</h1>
          <p className="mt-4 text-muted-foreground">快速上手梦帮小助，解答常见问题</p>
          <div className="mt-4 mx-auto w-20 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
        </motion.div>

        {/* Quick Start Guides */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-16"
        >
          <h2 className="text-xl font-display font-bold mb-6">快速入门</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {GUIDES.map((g) => (
              <Link
                key={g.title}
                href={g.href}
                className="group p-5 bg-card border border-border rounded-lg hover:border-primary/40 transition-colors"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
                    <g.icon size={16} className="text-primary" />
                  </div>
                  <h3 className="text-sm font-mono font-bold">{g.title}</h3>
                  <ChevronRight size={14} className="ml-auto text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{g.desc}</p>
              </Link>
            ))}
          </div>
        </motion.div>

        {/* FAQ */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mb-16"
        >
          <h2 className="text-xl font-display font-bold mb-6">常见问题</h2>
          <div className="space-y-4">
            {FAQ.map((item) => (
              <div key={item.q} className="p-5 bg-card border border-border rounded-lg">
                <h3 className="text-sm font-bold mb-2">{item.q}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{item.a}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Contact CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-center p-8 bg-card border border-border rounded-lg"
        >
          <Mail size={24} className="mx-auto mb-3 text-primary" />
          <h3 className="text-lg font-bold mb-2">没有找到答案？</h3>
          <p className="text-sm text-muted-foreground mb-4">联系我们的支持团队，我们会尽快回复</p>
          <Link
            href="/contact"
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-primary text-primary-foreground text-sm font-mono font-bold rounded-md hover:bg-primary/90 transition-colors"
          >
            联系我们
            <ChevronRight size={14} />
          </Link>
        </motion.div>
      </div>
    </div>
  )
}
