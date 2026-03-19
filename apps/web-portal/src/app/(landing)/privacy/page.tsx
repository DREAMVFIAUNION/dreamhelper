'use client'

import { motion } from 'framer-motion'

const SECTIONS = [
  {
    title: '1. 信息收集',
    content: `我们在您使用梦帮小助服务时，可能收集以下信息：

**账户信息：** 注册时提供的用户名、邮箱地址、密码（加密存储）。
**对话数据：** 您与 AI 助手的对话内容，用于提供服务和改善体验。
**知识库数据：** 您上传的文档内容，仅用于 RAG 检索服务。
**设备信息：** 浏览器类型、操作系统、IP 地址、访问时间（用于安全审计）。
**Cookie：** 必要的会话 Cookie 和功能性 Cookie（详见 Cookie 政策）。`,
  },
  {
    title: '2. 信息使用',
    content: `我们收集的信息仅用于以下目的：

- 提供、维护和改善梦帮小助 AI 服务
- 处理您的对话请求并生成 AI 回复
- 知识库文档的分块、索引和检索
- 账户安全验证和异常登录检测
- 服务质量监控和性能优化
- 遵守法律法规要求`,
  },
  {
    title: '3. 数据安全',
    content: `我们采取业界领先的安全措施保护您的数据：

**加密存储：** 所有敏感数据使用 AES-256-GCM 字段级加密。
**传输安全：** 全站 HTTPS 加密传输。
**访问控制：** 基于 RBAC 的权限管理，最小权限原则。
**审计日志：** 全操作审计日志记录，可追溯所有数据访问。
**密码安全：** 使用 bcrypt 算法哈希存储，不可逆。`,
  },
  {
    title: '4. 第三方服务',
    content: `为提供 AI 服务，我们可能将对话内容发送至以下第三方 AI 模型提供商进行处理：

- **MiniMax**（左脑逻辑推理）
- **阿里云通义千问 Qwen**（右脑创意发散）
- **智谱 GLM**（脑干质量监督）
- **Edge-TTS**（语音合成，微软服务）

这些第三方服务商有各自的隐私政策，我们已与其签署数据处理协议。对话数据仅用于即时处理，不会被第三方用于模型训练。`,
  },
  {
    title: '5. 数据保留',
    content: `- **对话数据：** 保留至您手动删除或账户注销。
- **知识库文档：** 保留至您手动删除。
- **账户信息：** 保留至账户注销后 30 天。
- **审计日志：** 保留 90 天。
- **Cookie：** 会话 Cookie 在浏览器关闭后失效；功能性 Cookie 保留 30 天。`,
  },
  {
    title: '6. 您的权利',
    content: `根据《个人信息保护法》(PIPL) 及相关法规，您享有以下权利：

- **访问权：** 查看我们收集的您的个人信息。
- **更正权：** 要求更正不准确的个人信息。
- **删除权：** 要求删除您的个人信息和对话数据。
- **导出权：** 以通用格式导出您的数据。
- **撤回同意：** 随时撤回对数据处理的同意。

行使上述权利，请联系 support@dreamvfia.com。`,
  },
  {
    title: '7. 未成年人保护',
    content: `梦帮小助服务面向 16 周岁及以上用户。如果我们发现未经监护人同意收集了未成年人信息，将立即删除相关数据。`,
  },
  {
    title: '8. 政策更新',
    content: `我们可能不时更新本隐私政策。重大变更将通过站内通知或邮件告知。继续使用服务即表示您接受更新后的政策。`,
  },
]

export default function PrivacyPage() {
  return (
    <div className="pt-24 pb-20">
      <div className="max-w-4xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">PRIVACY POLICY</p>
          <h1 className="text-3xl md:text-5xl font-display font-bold">隐私政策</h1>
          <p className="mt-4 text-sm text-muted-foreground">最后更新：2026 年 2 月 26 日</p>
          <div className="mt-4 mx-auto w-20 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="prose-sm"
        >
          <p className="text-sm text-muted-foreground leading-relaxed mb-8">
            DREAMVFIA（以下简称"我们"）非常重视您的隐私。本隐私政策说明我们如何收集、使用、存储和保护您的个人信息。
            使用梦帮小助服务即表示您同意本政策。
          </p>

          <div className="space-y-8">
            {SECTIONS.map((s, i) => (
              <motion.div
                key={s.title}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * i }}
                className="p-6 bg-card border border-border rounded-lg"
              >
                <h2 className="text-base font-bold mb-3">{s.title}</h2>
                <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                  {s.content.split(/\*\*([^*]+)\*\*/).map((part, j) =>
                    j % 2 === 1 ? <strong key={j} className="text-foreground">{part}</strong> : <span key={j}>{part}</span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
