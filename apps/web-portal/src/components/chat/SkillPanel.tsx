'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Zap, Search, Loader2, Copy, Check, X, ArrowLeft,
  Calculator, Briefcase, Code2, FileText, Gamepad2,
  Image, Music, Video, Sparkles, ChevronRight,
} from 'lucide-react'
import { useSkills, type SkillInfo, type SkillResult } from '@/hooks/useSkills'
import { cn } from '@/lib/utils'

// ── 分类配置: 标签 + 颜色 + 图标 ─────────────────────────
const CATEGORY_CONFIG: Record<string, {
  label: string
  icon: typeof Calculator
  color: string        // 主色 class
  bg: string           // 背景色 class
  border: string       // 边框色 class
  glow: string         // 发光 class
}> = {
  daily: {
    label: '日常', icon: Calculator,
    color: 'text-sky-400', bg: 'bg-sky-400/10', border: 'border-sky-400/25', glow: 'shadow-[0_0_8px_hsl(200_90%_60%/0.15)]',
  },
  office: {
    label: '办公', icon: Briefcase,
    color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/25', glow: 'shadow-[0_0_8px_hsl(160_80%_50%/0.15)]',
  },
  coding: {
    label: '编程', icon: Code2,
    color: 'text-violet-400', bg: 'bg-violet-400/10', border: 'border-violet-400/25', glow: 'shadow-[0_0_8px_hsl(270_80%_60%/0.15)]',
  },
  document: {
    label: '文档', icon: FileText,
    color: 'text-cyan-400', bg: 'bg-cyan-400/10', border: 'border-cyan-400/25', glow: 'shadow-[0_0_8px_hsl(180_80%_50%/0.15)]',
  },
  entertainment: {
    label: '娱乐', icon: Gamepad2,
    color: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400/25', glow: 'shadow-[0_0_8px_hsl(30_90%_55%/0.15)]',
  },
  image: {
    label: '图像', icon: Image,
    color: 'text-pink-400', bg: 'bg-pink-400/10', border: 'border-pink-400/25', glow: 'shadow-[0_0_8px_hsl(330_80%_60%/0.15)]',
  },
  audio: {
    label: '音频', icon: Music,
    color: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/25', glow: 'shadow-[0_0_8px_hsl(50_90%_55%/0.15)]',
  },
  video: {
    label: '视频', icon: Video,
    color: 'text-rose-400', bg: 'bg-rose-400/10', border: 'border-rose-400/25', glow: 'shadow-[0_0_8px_hsl(350_80%_60%/0.15)]',
  },
}

const DEFAULT_CAT = {
  label: '其他', icon: Sparkles,
  color: 'text-muted-foreground', bg: 'bg-muted/10', border: 'border-border', glow: '',
}

function getCatConfig(cat: string) {
  return CATEGORY_CONFIG[cat] || DEFAULT_CAT
}

// ── 组件 ──────────────────────────────────────────────────

interface SkillPanelProps {
  open: boolean
  onClose: () => void
  onInsertResult?: (text: string) => void
}

export function SkillPanel({ open, onClose, onInsertResult }: SkillPanelProps) {
  const { skills, categories, loading, executing, executeSkill, loadSkills } = useSkills()
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [selectedSkill, setSelectedSkill] = useState<SkillInfo | null>(null)
  const [params, setParams] = useState<Record<string, string>>({})
  const [result, setResult] = useState<SkillResult | null>(null)
  const [copied, setCopied] = useState(false)

  // 最近使用 (localStorage)
  const [recentNames, setRecentNames] = useState<string[]>([])
  useEffect(() => {
    try {
      const stored = localStorage.getItem('dreamhelp_recent_skills')
      if (stored) setRecentNames(JSON.parse(stored))
    } catch { /* ignore */ }
  }, [])

  const addRecent = useCallback((name: string) => {
    setRecentNames(prev => {
      const next = [name, ...prev.filter(n => n !== name)].slice(0, 6)
      try { localStorage.setItem('dreamhelp_recent_skills', JSON.stringify(next)) } catch { /* ignore */ }
      return next
    })
  }, [])

  if (!open) return null

  function handleSearch(q: string) {
    setSearchQuery(q)
    if (q) void loadSkills(q)
    else if (activeCategory) void loadSkills(undefined, activeCategory)
    else void loadSkills()
  }

  function handleCategoryFilter(cat: string | null) {
    setActiveCategory(cat)
    setSearchQuery('')
    if (cat) void loadSkills(undefined, cat)
    else void loadSkills()
  }

  function handleSelectSkill(skill: SkillInfo) {
    setSelectedSkill(skill)
    setParams({})
    setResult(null)
    addRecent(skill.name)
  }

  async function handleExecute() {
    if (!selectedSkill) return
    const r = await executeSkill(selectedSkill.name, params)
    setResult(r)
  }

  function handleCopy(text: string) {
    void navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  function getParamFields(skill: SkillInfo): Array<{ name: string; desc: string; type: string; default?: string }> {
    const schema = skill.parameters as { properties?: Record<string, { description?: string; type?: string; default?: unknown }> }
    if (!schema?.properties) return []
    return Object.entries(schema.properties).map(([name, prop]) => ({
      name,
      desc: prop.description || '',
      type: prop.type || 'string',
      default: prop.default !== undefined ? String(prop.default) : undefined,
    }))
  }

  // 最近使用的技能
  const recentSkills = recentNames
    .map(n => skills.find(s => s.name === n))
    .filter((s): s is SkillInfo => !!s)

  return (
    <div className="w-[340px] bg-card border-l border-border flex flex-col h-full">
      {/* ── 头部 ── */}
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-amber-400/15 border border-amber-400/30 flex items-center justify-center">
            <Zap size={12} className="text-amber-400" />
          </div>
          <div>
            <span className="text-xs font-bold text-foreground tracking-wide">技能中心</span>
            <span className="ml-1.5 text-[10px] font-mono text-muted-foreground">{skills.length} 个技能</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="w-6 h-6 rounded-md flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        >
          <X size={14} />
        </button>
      </div>

      {/* ── 搜索栏 ── */}
      <div className="px-4 py-2.5 border-b border-border">
        <div className="flex items-center gap-2 bg-secondary/60 border border-border px-3 py-1.5 rounded-lg">
          <Search size={13} className="text-muted-foreground flex-shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="搜索技能名称或功能..."
            className="flex-1 bg-transparent text-xs text-foreground placeholder:text-muted-foreground/40 outline-none"
          />
          {searchQuery && (
            <button onClick={() => handleSearch('')} className="text-muted-foreground hover:text-foreground">
              <X size={12} />
            </button>
          )}
        </div>
      </div>

      {/* ── 分类标签栏 ── */}
      <div className="px-4 py-2 flex gap-1.5 flex-wrap border-b border-border">
        <button
          onClick={() => handleCategoryFilter(null)}
          className={cn(
            'px-2.5 py-1 text-[10px] font-medium rounded-md border transition-all duration-200',
            !activeCategory
              ? 'bg-primary/10 border-primary/30 text-primary shadow-[0_0_6px_hsl(var(--primary)/0.2)]'
              : 'border-border text-muted-foreground hover:text-foreground hover:border-foreground/20',
          )}
        >
          全部
        </button>
        {Object.entries(categories).map(([cat, count]) => {
          const cfg = getCatConfig(cat)
          const CatIcon = cfg.icon
          const isActive = activeCategory === cat
          return (
            <button
              key={cat}
              onClick={() => handleCategoryFilter(cat)}
              className={cn(
                'px-2.5 py-1 text-[10px] font-medium rounded-md border transition-all duration-200 flex items-center gap-1',
                isActive
                  ? `${cfg.bg} ${cfg.border} ${cfg.color} ${cfg.glow}`
                  : 'border-border text-muted-foreground hover:text-foreground hover:border-foreground/20',
              )}
            >
              <CatIcon size={10} />
              {cfg.label}
              <span className="text-[8px] opacity-60">({count})</span>
            </button>
          )
        })}
      </div>

      {/* ── 内容区 ── */}
      <div className="flex-1 overflow-y-auto scrollbar-none">
        {selectedSkill ? (
          <SkillDetail
            skill={selectedSkill}
            params={params}
            result={result}
            executing={executing}
            copied={copied}
            onBack={() => setSelectedSkill(null)}
            onParamChange={(name, value) => setParams(prev => ({ ...prev, [name]: value }))}
            onExecute={handleExecute}
            onCopy={handleCopy}
            onInsert={onInsertResult}
            getParamFields={getParamFields}
          />
        ) : (
          <div className="p-3 space-y-4">
            {/* 最近使用 */}
            {!searchQuery && !activeCategory && recentSkills.length > 0 && (
              <div>
                <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2 px-1">
                  最近使用
                </div>
                <div className="flex gap-1.5 flex-wrap">
                  {recentSkills.map(skill => {
                    const cfg = getCatConfig(skill.category)
                    return (
                      <button
                        key={skill.name}
                        onClick={() => handleSelectSkill(skill)}
                        className={cn(
                          'px-2.5 py-1 text-[10px] font-mono rounded-md border transition-all duration-200',
                          cfg.border, cfg.bg, cfg.color, 'hover:brightness-125',
                        )}
                      >
                        {skill.name}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* 技能卡片网格 */}
            {loading ? (
              <div className="flex justify-center py-12">
                <Loader2 size={18} className="animate-spin text-muted-foreground" />
              </div>
            ) : skills.length === 0 ? (
              <div className="py-12 text-center text-xs text-muted-foreground/50">
                未找到匹配的技能
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {skills.map((skill) => {
                  const cfg = getCatConfig(skill.category)
                  const CatIcon = cfg.icon
                  return (
                    <button
                      key={skill.name}
                      onClick={() => handleSelectSkill(skill)}
                      className={cn(
                        'group text-left p-2.5 rounded-lg border transition-all duration-200',
                        'bg-card hover:translate-y-[-1px]',
                        cfg.border,
                        `hover:${cfg.glow}`,
                        'hover:border-opacity-50',
                      )}
                    >
                      <div className="flex items-start gap-2 mb-1.5">
                        <div className={cn('w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0', cfg.bg)}>
                          <CatIcon size={12} className={cfg.color} />
                        </div>
                        <ChevronRight size={10} className="text-muted-foreground/20 group-hover:text-muted-foreground ml-auto mt-1 flex-shrink-0 transition-colors" />
                      </div>
                      <div className="text-[11px] font-bold text-foreground truncate leading-tight">{skill.name}</div>
                      <div className="text-[9px] text-muted-foreground truncate mt-0.5 leading-tight">{skill.description}</div>
                      <div className={cn('mt-1.5 h-0.5 rounded-full w-full', cfg.bg)} />
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── 技能详情子组件 ─────────────────────────────────────────
interface SkillDetailProps {
  skill: SkillInfo
  params: Record<string, string>
  result: SkillResult | null
  executing: boolean
  copied: boolean
  onBack: () => void
  onParamChange: (name: string, value: string) => void
  onExecute: () => void
  onCopy: (text: string) => void
  onInsert?: (text: string) => void
  getParamFields: (skill: SkillInfo) => Array<{ name: string; desc: string; type: string; default?: string }>
}

function SkillDetail({
  skill, params, result, executing, copied,
  onBack, onParamChange, onExecute, onCopy, onInsert, getParamFields,
}: SkillDetailProps) {
  const cfg = getCatConfig(skill.category)
  const CatIcon = cfg.icon
  const fields = getParamFields(skill)

  return (
    <div className="p-4 space-y-4">
      {/* 返回 + 标题 */}
      <button onClick={onBack} className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-primary transition-colors">
        <ArrowLeft size={12} />
        <span>返回技能列表</span>
      </button>

      <div className="flex items-start gap-3">
        <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', cfg.bg, cfg.border, 'border')}>
          <CatIcon size={18} className={cfg.color} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-bold text-foreground">{skill.name}</div>
          <div className="text-[11px] text-muted-foreground mt-0.5">{skill.description}</div>
          <div className={cn('inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded text-[9px] font-medium', cfg.bg, cfg.color)}>
            <CatIcon size={9} />
            {cfg.label}
          </div>
        </div>
      </div>

      {/* 参数表单 */}
      {fields.length > 0 && (
        <div className="space-y-2.5">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">参数</div>
          {fields.map((field) => (
            <div key={field.name} className="space-y-1">
              <label className="flex items-baseline gap-1.5">
                <span className="text-[11px] font-mono font-bold text-foreground">{field.name}</span>
                {field.desc && <span className="text-[9px] text-muted-foreground">{field.desc}</span>}
              </label>
              <input
                type="text"
                value={params[field.name] ?? field.default ?? ''}
                onChange={(e) => onParamChange(field.name, e.target.value)}
                placeholder={field.default || `输入 ${field.name}...`}
                className="w-full bg-secondary/60 border border-border px-3 py-1.5 text-xs text-foreground rounded-lg outline-none focus:border-primary/40 focus:shadow-[0_0_6px_hsl(var(--primary)/0.15)] transition-all"
              />
            </div>
          ))}
        </div>
      )}

      {/* 执行按钮 */}
      <button
        onClick={onExecute}
        disabled={executing}
        className={cn(
          'w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition-all duration-200',
          cfg.bg, cfg.border, cfg.color, 'border',
          executing ? 'opacity-50 cursor-not-allowed' : `hover:brightness-125 ${cfg.glow}`,
        )}
      >
        {executing ? <Loader2 size={13} className="animate-spin" /> : <Zap size={13} />}
        {executing ? '执行中...' : '执行技能'}
      </button>

      {/* 结果 */}
      {result && (
        <div className={cn(
          'p-3 border rounded-lg text-xs',
          result.success
            ? 'bg-emerald-500/5 border-emerald-500/20 text-foreground'
            : 'bg-destructive/5 border-destructive/20 text-destructive',
        )}>
          <div className="flex items-center justify-between mb-2">
            <span className="font-bold text-[11px]">{result.success ? '执行结果' : '执行失败'}</span>
            {result.result && (
              <button
                onClick={() => onCopy(result.result!)}
                className="flex items-center gap-1 text-muted-foreground hover:text-primary text-[10px] transition-colors"
              >
                {copied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                {copied ? '已复制' : '复制'}
              </button>
            )}
          </div>
          <pre className="whitespace-pre-wrap break-all max-h-60 overflow-y-auto scrollbar-none font-mono text-[11px] leading-relaxed">
            {result.success ? result.result : result.error}
          </pre>
          {result.result && onInsert && (
            <button
              onClick={() => onInsert(result.result!)}
              className={cn(
                'mt-2.5 w-full flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-[10px] font-bold transition-all',
                'border border-sky-400/20 text-sky-400 hover:bg-sky-400/10',
              )}
            >
              <Sparkles size={10} />
              插入到对话
            </button>
          )}
        </div>
      )}
    </div>
  )
}
