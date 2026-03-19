'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import {
  Bot, Code, Pen, BarChart3, Wrench, Zap, Plus, Trash2, Edit3, RefreshCw,
  ChevronDown, ChevronUp, Sparkles, Globe, Lock,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'

interface AgentData {
  id: string
  name: string
  description: string
  type: string
  systemPrompt: string
  modelProvider: string
  modelName: string
  temperature: number
  maxTokens: number
  capabilities: string[]
  tools: string[]
  status: string
  isPublic: boolean
  usageCount: number
  createdAt: string
  updatedAt: string
}

const TYPE_CONFIG: Record<string, { icon: typeof Bot; color: string; bgColor: string }> = {
  code:     { icon: Code,     color: 'text-cyan-400',    bgColor: 'bg-cyan-500/10' },
  writing:  { icon: Pen,      color: 'text-purple-400',  bgColor: 'bg-purple-500/10' },
  analysis: { icon: BarChart3, color: 'text-yellow-400', bgColor: 'bg-yellow-500/10' },
  general:  { icon: Bot,      color: 'text-green-400',   bgColor: 'bg-green-500/10' },
  custom:   { icon: Wrench,   color: 'text-primary',     bgColor: 'bg-primary/10' },
}

export default function AgentsPage() {
  const t = useTranslations('agents')
  const tc = useTranslations('common')
  const [agents, setAgents] = useState<AgentData[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  const fetchAgents = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await fetch('/api/agents')
      if (resp.ok) {
        const data = await resp.json()
        setAgents(data.data || [])
      }
    } catch { /* backend unavailable */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchAgents() }, [fetchAgents])

  const handleDelete = async (id: string) => {
    if (!confirm(t('confirmDelete'))) return
    await fetch(`/api/agents/${id}`, { method: 'DELETE' })
    setAgents((prev) => prev.filter((a) => a.id !== id))
  }

  const handleSeedPresets = async () => {
    setLoading(true)
    await fetch('/api/agents/seed-presets', { method: 'POST' }).catch(() => {})
    await fetchAgents()
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-1 h-8 bg-primary rounded-full shadow-[0_0_8px_hsl(var(--primary)/0.4)]" />
          <div>
            <h1 className="font-display text-xl font-bold text-foreground tracking-wider">{t('title')}</h1>
            <p className="text-xs font-mono text-muted-foreground mt-0.5">{t('subtitle')}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon-sm" onClick={fetchAgents} disabled={loading}>
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          </Button>
          <Button variant="cyber" size="sm" onClick={() => setShowCreate(!showCreate)} className="font-mono text-xs gap-1.5">
            <Plus size={12} /> {t('create')}
          </Button>
        </div>
      </div>

      {/* Smart Routing Info */}
      <Card className="border-primary/20">
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-1.5">
            <Zap size={14} className="text-primary" />
            <span className="text-xs font-mono font-bold text-foreground">{t('smartRouting')}</span>
          </div>
          <p className="text-[11px] font-mono text-muted-foreground leading-relaxed whitespace-pre-line">
            {t('smartRoutingDesc')}
          </p>
        </CardContent>
      </Card>

      {/* Create Form */}
      {showCreate && (
        <CreateAgentForm
          onCreated={() => { setShowCreate(false); fetchAgents() }}
          onCancel={() => setShowCreate(false)}
        />
      )}

      {/* Agent Cards */}
      {loading && agents.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground text-sm font-mono">
          <RefreshCw size={20} className="animate-spin mx-auto mb-2" />
          {tc('loading')}
        </div>
      ) : agents.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <Bot size={40} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm font-mono mb-3">{t('noAgents')}</p>
          <Button variant="cyber" size="sm" onClick={handleSeedPresets} className="font-mono text-xs gap-1.5">
            <Sparkles size={12} /> {t('loadPresets')}
          </Button>
        </div>
      ) : (
        <div className="grid gap-3">
          {agents.map((agent) => {
            const cfg = TYPE_CONFIG[agent.type] ?? TYPE_CONFIG['custom']!
            const Icon = cfg.icon
            const expanded = expandedId === agent.id

            return (
              <Card
                key={agent.id}
                className={cn(
                  'overflow-hidden transition-all',
                  agent.status !== 'active' && 'opacity-60',
                )}
              >
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-accent/30 transition-colors"
                  onClick={() => setExpandedId(expanded ? null : agent.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center', cfg.bgColor)}>
                      <Icon size={18} className={cfg.color} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-foreground">{agent.name}</span>
                        {agent.isPublic ? (
                          <span className="text-green-400" aria-label="公开"><Globe size={11} /></span>
                        ) : (
                          <span className="text-muted-foreground" aria-label="私有"><Lock size={11} /></span>
                        )}
                        <Badge variant={agent.status === 'active' ? 'success' : 'secondary'} className="text-[9px] px-1.5 py-0 h-4">
                          {agent.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">{agent.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right text-[10px] font-mono text-muted-foreground hidden sm:block">
                      <div>{agent.modelName}</div>
                      <div>T={agent.temperature}</div>
                    </div>
                    {expanded ? <ChevronUp size={14} className="text-muted-foreground" /> : <ChevronDown size={14} className="text-muted-foreground" />}
                  </div>
                </div>

                {expanded && (
                  <div className="px-4 pb-4 border-t border-border space-y-3">
                    <div className="grid grid-cols-2 gap-3 mt-3 text-xs font-mono">
                      <div>
                        <div className="text-muted-foreground mb-1">{t('model')}</div>
                        <div className="text-secondary-foreground">{agent.modelProvider} / {agent.modelName}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground mb-1">{t('params')}</div>
                        <div className="text-secondary-foreground">{t('temp')} {agent.temperature} · {t('maxTokens', { n: agent.maxTokens })}</div>
                      </div>
                    </div>
                    {agent.systemPrompt && (
                      <div>
                        <div className="text-[10px] font-mono text-muted-foreground mb-1">System Prompt</div>
                        <div className="bg-secondary rounded-md p-2.5 text-xs text-secondary-foreground font-mono leading-relaxed max-h-32 overflow-y-auto">
                          {agent.systemPrompt}
                        </div>
                      </div>
                    )}
                    <div className="flex items-center gap-2 flex-wrap">
                      {agent.capabilities.map((c) => (
                        <Badge key={c} variant="secondary" className="text-[9px] px-1.5 py-0 h-4">{c}</Badge>
                      ))}
                      {agent.tools.map((tool) => (
                        <Badge key={tool} variant="cyber" className="text-[9px] px-1.5 py-0 h-4">{tool}</Badge>
                      ))}
                    </div>
                    <div className="flex items-center gap-2 pt-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => { e.stopPropagation(); handleDelete(agent.id) }}
                        className="text-destructive/70 hover:text-destructive text-[10px] font-mono gap-1"
                      >
                        <Trash2 size={11} /> {tc('delete')}
                      </Button>
                    </div>
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

/** 快速创建表单 */
function CreateAgentForm({ onCreated, onCancel }: { onCreated: () => void; onCancel: () => void }) {
  const t = useTranslations('agents')
  const tc = useTranslations('common')
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [type, setType] = useState('custom')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!name.trim()) return
    setSubmitting(true)
    try {
      const resp = await fetch('/api/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          description: desc.trim(),
          type,
          system_prompt: systemPrompt.trim(),
        }),
      })
      if (resp.ok) onCreated()
    } finally { setSubmitting(false) }
  }

  return (
    <Card className="border-primary/30">
      <CardContent className="p-4 space-y-3">
        <h3 className="text-sm font-mono font-bold text-foreground">{t('createAgent')}</h3>
        <div className="grid grid-cols-2 gap-3">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={t('agentName')}
            className="font-mono text-xs"
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="bg-secondary rounded-md px-3 py-2 text-xs font-mono text-foreground border border-border focus:border-primary/50 outline-none"
          >
            <option value="custom">{t('typeCustom')}</option>
            <option value="code">{t('typeCode')}</option>
            <option value="writing">{t('typeWriting')}</option>
            <option value="analysis">{t('typeAnalysis')}</option>
            <option value="general">{t('typeGeneral')}</option>
          </select>
        </div>
        <Input
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
          placeholder={t('shortDesc')}
          className="font-mono text-xs"
        />
        <Textarea
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          placeholder="System Prompt (可选)"
          rows={3}
          className="font-mono text-xs resize-none"
        />
        <div className="flex items-center gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={onCancel} className="font-mono text-xs">
            {tc('cancel')}
          </Button>
          <Button
            variant="cyber"
            size="sm"
            onClick={handleSubmit}
            disabled={!name.trim() || submitting}
            className="font-mono text-xs"
          >
            {submitting ? t('creating') : t('create')}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
