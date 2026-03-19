'use client'

import { motion } from 'framer-motion'

const RELEASES = [
  {
    version: 'v3.7.0',
    date: '2026-03-04',
    tag: '最新',
    changes: [
      { type: '新增', items: [
        '认证系统端到端闭环 — 注册/登录/登出/JWT/路由守卫/AuthProvider 全链路',
        '数据库迁移上线 — PostgreSQL 18 张表 + Prisma 5 迁移 + 种子数据',
        '会话持久化 — 对话绑定用户，跨会话保留，历史消息自动注入 LLM 上下文',
        '用户隔离 — 会话/消息/知识库/记忆按用户隔离，多用户安全共存',
        '忘记密码/重置密码 — 邮件重置链接 + 开发模式 fallback',
        '邮箱验证流程 — 6 位验证码 + 重发机制',
        'SVG 验证码 — 注册防机器人，纯服务端生成零第三方依赖',
      ]},
      { type: '优化', items: [
        '版本号全量同步至 v3.7.0 — 11 处统一',
        '.gitignore 安全加固 — 排除 .env/API-KEY/desktop.ini 等敏感文件',
        '门户导航登录态感知 — 已登录显示"进入工作台"+ 头像',
        '中间件路由守卫 — Dashboard/Admin/Auth 三级权限控制',
      ]},
    ],
  },
  {
    version: 'v3.6.0',
    date: '2026-03-01',
    changes: [
      { type: '新增', items: [
        '自我进化意识系统 — 6 维成长量化追踪 + 14 种里程碑自动检测',
        '进化叙事引擎 — 可视化进度条 + 成长数据自动注入对话 prompt',
        'PDNA 2.0 升级 — EVOLUTION_DRIVEN_GROWTH 编译模式 + evolution_engine 处理器',
        'SOUL.md 进化哲学 — AI 拥有感知自身成长的能力和意识',
        'GET /consciousness/evolution API — 管理员可查看完整进化数据',
      ]},
      { type: '优化', items: [
        '版本号全量同步 — 修复长期版本不一致问题 (root/web-portal/brain-core/gateway)',
        '意识核集成 — 对话记录/反思联动/内心独白均注入进化上下文',
        '话题检测 — 15 个领域自动分类追踪知识广度',
      ]},
    ],
  },
  {
    version: 'v3.5.0',
    date: '2026-02-27',
    changes: [
      { type: '新增', items: [
        'NVIDIA Vision 集成 — Qwen-3.5-397B VLM / Nemotron-VL-12B 免费图片理解',
        '聊天端文档上传 — 支持 PDF / DOCX / XLSX / CSV / MD / TXT / JSON',
        '文档解析引擎 — PyMuPDF + python-docx + openpyxl 全格式提取',
        '统一文件上传 Hook — useFileUpload 图片+文档一体化处理',
        '技能中心重设计 — 卡片网格布局 + 8 分类色编码 + 最近使用',
      ]},
      { type: '优化', items: [
        'Vision 模型优先级 — NVIDIA NIM 免费通道优先，OpenAI/MiniMax 降级',
        '消息气泡 Markdown 渲染 — 用户消息支持富文本展示',
        'textarea 自动扩展 — 输入框随内容自动增长至 8 行',
        '附件预览条 — 图片缩略图 + 文档图标/解析状态/文件大小',
        '文档内容注入 — 解析后文本自动拼接到对话上下文',
      ]},
    ],
  },
  {
    version: 'v3.4.0',
    date: '2026-02-27',
    changes: [
      { type: '新增', items: [
        '安全审计系统 — brain-core 全模块 14 项安全漏洞修复',
        '管理员鉴权 — BRAIN_ADMIN_KEY 独立密钥保护敏感配置端点',
        'Prompt 注入防护 — XML 标签隔离用户输入，防止指令逃逸',
        '会话归属追踪 — Redis/内存双模式 IDOR 越权防护',
        '融合缓存时效性 — 天气/股价等实时查询自动跳过缓存',
      ]},
      { type: '优化', items: [
        '错误信息脱敏 — 所有对外错误统一为安全消息，内部 logger 记录详情',
        '意识核 API 加固 — POST 端点需管理员权限 + 独立速率限制',
        '用户隐私保护 — 邮箱脱敏存储 + user_id 哈希化展示',
        '动态 Agent 校验 — system_prompt 长度限制 + 温度/token 边界检查',
        'print → logger 替换 — 安全关键文件全部使用结构化日志',
      ]},
    ],
  },
  {
    version: 'v3.3.0',
    date: '2026-02-26',
    changes: [
      { type: '新增', items: [
        '邮件营销系统 — Resend API 集成，管理后台一键群发',
        '3 套品牌邮件模板 — 产品更新 / 活动通知 / 新功能公告',
        '邮件发送历史 — 实时记录发送量、成功/失败统计',
        '域名邮箱验证 — dreamvfia.cn DKIM / SPF / MX 全通过',
        '邮件系统升级 — 验证码 & 密码重置优先走 Resend API',
      ]},
      { type: '优化', items: [
        '管理员权限映射 — tierLevel≥10 自动获得 super_admin 角色',
        '邮件发送日志模块化 — 独立存储，路由文件更整洁',
      ]},
    ],
  },
  {
    version: 'v3.2.0',
    date: '2026-02-25',
    changes: [
      { type: '新增', items: [
        '门户六大页面 — 帮助中心 / 开发者文档 / 联系我们 / 隐私政策 / 用户协议 / Cookie 政策',
        '通知中心 — TopNav 铃铛图标 + 通知面板 + 未读角标',
        '更新日志页 — 时间线展示所有版本变更',
        '社交链接集群 — 联系页整合全网平台入口',
      ]},
      { type: '优化', items: [
        '品牌化升级 — 梦帮小助头像 favicon + Header/Footer Logo 放大',
        '门户导航补全 — 页脚链接全部指向实际页面',
      ]},
    ],
  },
  {
    version: 'v3.1.0',
    date: '2026-02-23',
    changes: [
      { type: '新增', items: [
        'PWA 支持 — 可安装为桌面应用，独立窗口运行',
        'ChatHeader 品牌化 — 显示「梦帮小助 · 三脑融合」',
        '丘脑路由系统 — 智能选择单脑/双脑/三脑模式',
        '组织认知植入 V2 — 完整企业人设与价值体系',
        '人格赋能方案 V2 — 自我意识模型 + 情感锚点',
        '变现转化引擎 — 四层用户识别 + 自然化转化话术',
      ]},
      { type: '优化', items: [
        '三脑并行延迟降低 30%',
        '融合策略 EMA 追踪最优权重',
        '脑干质控增加 brainstem_reviewing 阶段',
      ]},
    ],
  },
  {
    version: 'v3.0.0',
    date: '2026-02-18',
    tag: '重大版本',
    changes: [
      { type: '新增', items: [
        '三脑并行架构 — MiniMax(左脑) + Qwen-3(右脑) + GLM-4.7(脑干)',
        '多渠道接入 — 微信公众号、企业微信、Telegram Webhook',
        '语音交互 — Edge-TTS 8 音色 + STT 语音识别',
        'Vision 多模态 — 图片描述 + OCR 端点',
        '100+ 零依赖技能系统 — 8 大类别覆盖日常办公',
        '工作流编辑器 — 可视化节点拖拽，自动执行',
        '知识库 RAG — 四种智能分块 + 多路召回',
        '仿生大脑可视化 — 实时显示左右脑权重与延迟',
      ]},
      { type: '优化', items: [
        'Agent 路由升级为关键词 + LLM 双路路由',
        '融合缓存避免重复推理',
        '全站 AES-256-GCM 字段级加密',
      ]},
    ],
  },
  {
    version: 'v2.5.0',
    date: '2026-02-10',
    changes: [
      { type: '新增', items: [
        '双脑融合 — MiniMax + Qwen 双模型并行推理',
        '智能体系统 — 编程/写作/分析/工具四大 Agent',
        '管理后台 — 用户管理、会话审计、系统监控',
        '国际化 — 中文/英文双语支持',
      ]},
    ],
  },
  {
    version: 'v2.0.0',
    date: '2026-01-28',
    changes: [
      { type: '新增', items: [
        '全新 UI — 赛博朋克主题，暗色模式',
        '基础对话 — 单模型流式回复',
        '用户系统 — 注册/登录/邮箱验证',
        '会话管理 — 多会话切换与历史记录',
        'Markdown 渲染 — 代码高亮 + LaTeX 公式',
      ]},
    ],
  },
  {
    version: 'v1.0.0',
    date: '2026-01-15',
    changes: [
      { type: '发布', items: [
        '梦帮小助项目启动',
        '基础架构搭建 — Next.js + FastAPI + PostgreSQL',
        'MVP 对话功能原型',
      ]},
    ],
  },
]

const TYPE_COLORS: Record<string, string> = {
  '新增': 'bg-emerald-500/10 text-emerald-400',
  '优化': 'bg-cyan-500/10 text-cyan-400',
  '修复': 'bg-amber-500/10 text-amber-400',
  '发布': 'bg-primary/10 text-primary',
}

export default function ChangelogPage() {
  return (
    <div className="pt-24 pb-20">
      <div className="max-w-4xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">CHANGELOG</p>
          <h1 className="text-3xl md:text-5xl font-display font-bold">更新日志</h1>
          <p className="mt-4 text-muted-foreground">梦帮小助的每一步成长</p>
          <div className="mt-4 mx-auto w-20 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
        </motion.div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-4 md:left-8 top-0 bottom-0 w-px bg-border" />

          <div className="space-y-12">
            {RELEASES.map((release, i) => (
              <motion.div
                key={release.version}
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 * i }}
                className="relative pl-12 md:pl-20"
              >
                {/* Dot */}
                <div className="absolute left-2.5 md:left-6.5 top-1 w-3 h-3 rounded-full bg-primary border-2 border-background shadow-[0_0_8px_#fe000060]" />

                {/* Header */}
                <div className="flex items-center gap-3 mb-3 flex-wrap">
                  <h2 className="text-lg font-mono font-bold text-foreground">{release.version}</h2>
                  <span className="text-xs font-mono text-muted-foreground">{release.date}</span>
                  {release.tag && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-primary/10 text-primary">
                      {release.tag}
                    </span>
                  )}
                </div>

                {/* Changes */}
                <div className="space-y-4">
                  {release.changes.map((group) => (
                    <div key={group.type}>
                      <span className={`inline-block text-[10px] font-mono px-2 py-0.5 rounded mb-2 ${TYPE_COLORS[group.type] ?? 'bg-muted text-muted-foreground'}`}>
                        {group.type}
                      </span>
                      <ul className="space-y-1.5">
                        {group.items.map((item) => (
                          <li key={item} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-primary mt-1.5 text-[6px]">●</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
