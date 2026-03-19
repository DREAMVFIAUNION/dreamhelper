'use client'

import { motion } from 'framer-motion'
import { Code, Key, Webhook, Server, Terminal, BookOpen } from 'lucide-react'

const SECTIONS = [
  {
    icon: Server,
    title: 'API 概览',
    content: `梦帮小助提供 RESTful API，基础地址为 \`/api\`。所有 API 均需通过 JWT Bearer Token 认证。

**认证方式：**
- 登录获取 JWT Token（Cookie 自动携带）
- 或在「设置 → API Key」生成长期有效的 API Key
- Header: \`Authorization: Bearer <token>\``,
  },
  {
    icon: Terminal,
    title: '对话 API',
    content: `**POST /api/chat/completions**

发送消息并获得 AI 回复（支持流式 SSE）。

\`\`\`json
{
  "session_id": "uuid",
  "message": "你好",
  "stream": true
}
\`\`\`

**SSE 事件类型：**
- \`text\` — 文本内容
- \`thinking\` — 思考过程
- \`brain_start / brain_done\` — 三脑状态
- \`tool_start / tool_result\` — 工具调用
- \`done\` — 结束`,
  },
  {
    icon: Key,
    title: '认证 API',
    content: `**POST /api/auth/login** — 邮箱密码登录
**POST /api/auth/register** — 注册新用户
**POST /api/auth/logout** — 退出登录
**GET /api/auth/me** — 获取当前用户信息
**POST /api/auth/verify-email** — 验证邮箱
**POST /api/auth/forgot-password** — 忘记密码`,
  },
  {
    icon: BookOpen,
    title: '知识库 API',
    content: `**GET /api/knowledge** — 获取知识库列表
**POST /api/knowledge/upload** — 上传文档（multipart/form-data）
**DELETE /api/knowledge/:id** — 删除文档

支持格式：PDF、Markdown、TXT、DOCX
自动分块策略：文本 / Markdown / 代码 / FAQ 四种模式`,
  },
  {
    icon: Webhook,
    title: '多渠道 Webhook 接入',
    content: `支持三种外部渠道接入，消息自动路由至三脑核心：

**微信公众号**
- 验证：\`GET /api/v1/webhook/wechat\`
- 消息：\`POST /api/v1/webhook/wechat\`
- 环境变量：\`WECHAT_APP_ID\`, \`WECHAT_TOKEN\`

**企业微信**
- 验证：\`GET /api/v1/webhook/wecom\`
- 消息：\`POST /api/v1/webhook/wecom\`
- 环境变量：\`WECOM_CORP_ID\`, \`WECOM_TOKEN\`

**Telegram Bot**
- Webhook：\`POST /api/v1/webhook/telegram\`
- 环境变量：\`TELEGRAM_BOT_TOKEN\`, \`TELEGRAM_WEBHOOK_SECRET\``,
  },
  {
    icon: Code,
    title: '技术栈',
    content: `**前端：** Next.js 15 + React 19 + TailwindCSS + shadcn/ui
**后端：** FastAPI (brain-core) + NestJS (gateway)
**数据库：** PostgreSQL + Prisma ORM + Redis
**AI 模型：** MiniMax-M2.5 / Qwen-3 / GLM-4.7（三脑并行）
**RAG：** 向量检索 + 多路召回 + 查询改写
**语音：** Edge-TTS + faster-whisper (可选)
**部署：** Docker Compose / PM2`,
  },
]

export default function DocsPage() {
  return (
    <div className="pt-24 pb-20">
      <div className="max-w-4xl mx-auto px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">DEVELOPER DOCS</p>
          <h1 className="text-3xl md:text-5xl font-display font-bold">开发者文档</h1>
          <p className="mt-4 text-muted-foreground">API 接入指南与技术参考</p>
          <div className="mt-4 mx-auto w-20 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
        </motion.div>

        {/* Sections */}
        <div className="space-y-8">
          {SECTIONS.map((s, i) => (
            <motion.div
              key={s.title}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * i }}
              className="p-6 bg-card border border-border rounded-lg"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
                  <s.icon size={16} className="text-primary" />
                </div>
                <h2 className="text-base font-mono font-bold">{s.title}</h2>
              </div>
              <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line font-mono">
                {s.content.split(/(`[^`]+`)/g).map((part, j) =>
                  part.startsWith('`') && part.endsWith('`') ? (
                    <code key={j} className="px-1.5 py-0.5 bg-muted rounded text-xs text-primary">
                      {part.slice(1, -1)}
                    </code>
                  ) : part.startsWith('```') ? (
                    <pre key={j} className="mt-2 mb-2 p-3 bg-muted rounded text-xs overflow-x-auto">
                      {part.replace(/```\w*\n?/, '').replace(/```$/, '')}
                    </pre>
                  ) : (
                    <span key={j}>{part.replace(/\*\*([^*]+)\*\*/g, '').split(/\*\*([^*]+)\*\*/).length > 1
                      ? part.split(/\*\*([^*]+)\*\*/).map((seg, k) =>
                          k % 2 === 1 ? <strong key={k} className="text-foreground">{seg}</strong> : seg
                        )
                      : part
                    }</span>
                  )
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
