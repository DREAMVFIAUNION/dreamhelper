'use client'

import { useState } from 'react'
import { CheckCircle, AlertCircle, Server, Database, Brain, Globe, Cpu, HardDrive } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ServiceStatus {
  name: string
  icon: React.ReactNode
  status: 'ok' | 'warn' | 'error'
  detail: string
}

const SERVICES: ServiceStatus[] = [
  { name: 'Web Portal (Next.js)', icon: <Globe size={14} />, status: 'ok', detail: 'localhost:3000 · 55+ routes' },
  { name: 'Brain Core (FastAPI)', icon: <Brain size={14} />, status: 'ok', detail: 'localhost:8000 · Triple Brain + RAG + MCP' },
  { name: 'PostgreSQL', icon: <Database size={14} />, status: 'ok', detail: 'Prisma ORM · 8 models' },
  { name: 'LLM Provider', icon: <Cpu size={14} />, status: 'ok', detail: 'Triple Brain: MiniMax + Qwen-3 + GLM-4.7' },
  { name: 'MCP 外接工具', icon: <Server size={14} />, status: 'ok', detail: '4 服务器 · 36 工具 (思维链/文件系统/知识图谱/Windows自动化)' },
  { name: 'Object Storage', icon: <HardDrive size={14} />, status: 'warn', detail: '本地文件系统 · 待接入 S3/MinIO' },
]

const ENV_VARS = [
  { key: 'DATABASE_URL', desc: 'PostgreSQL 连接', masked: true },
  { key: 'JWT_SECRET', desc: 'JWT 签名密钥', masked: true },
  { key: 'MINIMAX_API_KEY', desc: 'MiniMax API 密钥', masked: true },
  { key: 'GLM_API_KEY', desc: 'GLM-4.7 (脑干)', masked: true },
  { key: 'DEEPSEEK_API_KEY', desc: 'DeepSeek API', masked: true },
  { key: 'MCP_ENABLED', desc: 'MCP 外接工具', masked: false, value: 'true' },
  { key: 'BRAIN_CORE_URL', desc: 'Brain Core 地址', masked: false, value: 'http://127.0.0.1:8000' },
  { key: 'NODE_ENV', desc: '运行环境', masked: false, value: 'development' },
]

const SYSTEM_INFO = [
  { label: '版本', value: 'v3.7.0' },
  { label: '前端框架', value: 'Next.js 15 + React 19' },
  { label: '后端框架', value: 'FastAPI + NestJS' },
  { label: '数据库', value: 'PostgreSQL + Prisma 5' },
  { label: '样式系统', value: 'TailwindCSS + 赛博朋克主题' },
  { label: '技能数', value: '90 (日常15+办公15+编程15+文档13+娱乐12+图像12+视频8)' },
  { label: 'Agent 数', value: '4 (ReAct/Code/Writing/Analysis)' },
  { label: 'MCP 工具', value: '36 (思维链1+文件系统14+知识图谱9+Windows12)' },
  { label: 'API 路由', value: '55+' },
  { label: '页面路由', value: '30+' },
]

export default function AdminSystemPage() {
  const [showMasked, setShowMasked] = useState(false)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-mono font-bold text-foreground">系统设置</h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">全局系统配置与服务状态</p>
      </div>

      {/* 服务状态 */}
      <div className="bg-card border border-border p-4 rounded-md">
        <h2 className="text-sm font-mono font-bold text-foreground mb-3">服务状态</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {SERVICES.map((s) => (
            <div key={s.name} className="flex items-center gap-2.5 px-3 py-2 bg-secondary border border-border/50 rounded-md">
              <div className="text-muted-foreground/60">{s.icon}</div>
              <div className="flex-1 min-w-0">
                <div className="text-[10px] font-mono font-bold text-foreground">{s.name}</div>
                <div className="text-[9px] font-mono text-muted-foreground/50">{s.detail}</div>
              </div>
              {s.status === 'ok' ? (
                <CheckCircle size={13} className="text-emerald-400 flex-shrink-0" />
              ) : (
                <AlertCircle size={13} className="text-yellow-500 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 系统信息 */}
      <div className="bg-card border border-border p-4 rounded-md">
        <h2 className="text-sm font-mono font-bold text-foreground mb-3">系统信息</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-1.5">
          {SYSTEM_INFO.map((item) => (
            <div key={item.label} className="flex items-baseline gap-2 text-[10px] font-mono">
              <span className="text-muted-foreground/60">{item.label}:</span>
              <span className="text-foreground">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 环境变量 */}
      <div className="bg-card border border-border p-4 rounded-md">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-mono font-bold text-foreground">环境变量</h2>
          <button
            onClick={() => setShowMasked(!showMasked)}
            className="text-[9px] font-mono text-muted-foreground hover:text-primary transition-colors"
          >
            {showMasked ? '隐藏敏感值' : '显示敏感值'}
          </button>
        </div>
        <div className="space-y-1">
          {ENV_VARS.map((v) => (
            <div key={v.key} className="flex items-center gap-3 px-3 py-1.5 bg-secondary border border-border/30 text-[10px] font-mono rounded-md">
              <span className="text-sky-400 font-bold w-36 flex-shrink-0">{v.key}</span>
              <span className="text-muted-foreground/50 flex-shrink-0 w-28">{v.desc}</span>
              <span className={cn('text-muted-foreground truncate', v.masked && !showMasked && 'select-none')}>
                {v.masked && !showMasked ? '••••••••••••' : (v.value || '(env)')}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
