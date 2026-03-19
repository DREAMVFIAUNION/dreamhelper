'use client'

import { useEffect, useState } from 'react'
import { Brain, Heart, Target, Globe, Sparkles, RefreshCw, Shield, Users } from 'lucide-react'
import { cn } from '@/lib/utils'
import { EmotionIndicator } from './EmotionIndicator'
import { GoalTracker } from './GoalTracker'
import { OpinionList } from './OpinionList'

interface ConsciousnessStatus {
  enabled: boolean
  started: boolean
  self_model: { name: string; total_conversations: number; total_reflections: number; opinions_count: number }
  emotion: { mood: string; valence: number; arousal: number; curiosity: number; confidence: number; engagement: number }
  world_model: { has_weather: boolean; has_news: boolean; has_market: boolean; has_crypto: boolean; last_observed: number }
  goals: { total_goals: number; active_goals: number; completed_goals: number }
  inner_voice: { think_count: number; total_thoughts: number; expressed_thoughts: number }
  value_anchor: { tracked_users: number; expressions_24h: number }
  consistency?: { current_scene: string; turn_count: number; drift_count: number }
  conversion?: { tracked_users: number; conversation_hooks_used: number }
}

export function ConsciousnessPanel() {
  const [status, setStatus] = useState<ConsciousnessStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'opinions'>('overview')

  const fetchStatus = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/consciousness/status')
      if (res.ok) setStatus(await res.json())
    } catch { /* silent */ } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 60_000)
    return () => clearInterval(interval)
  }, [])

  if (!status) {
    return (
      <div className="p-4 text-xs text-muted-foreground font-mono">
        意识核加载中...
      </div>
    )
  }

  if (!status.enabled || !status.started) {
    return (
      <div className="p-4 text-xs text-muted-foreground font-mono">
        意识核未启动
      </div>
    )
  }

  const { emotion, inner_voice, goals, world_model, self_model, consistency, conversion } = status

  return (
    <div className="p-3 space-y-4 text-sm">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain size={16} className="text-primary" />
          <span className="font-mono font-bold text-primary text-xs">CONSCIOUSNESS</span>
        </div>
        <button
          onClick={fetchStatus}
          disabled={loading}
          className="text-muted-foreground hover:text-primary transition-colors"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1">
        {(['overview', 'opinions'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'text-[10px] font-mono px-2 py-0.5 rounded transition-colors',
              activeTab === tab
                ? 'bg-primary/10 text-primary border border-primary/30'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {tab === 'overview' ? '总览' : '观点'}
          </button>
        ))}
      </div>

      {activeTab === 'overview' ? (
        <>
          {/* Emotion Orb + Bars */}
          <div className="flex items-start gap-3">
            <EmotionIndicator emotion={emotion} size={52} />
            <div className="flex-1 space-y-1">
              {[
                { label: '正负', value: emotion.valence, color: 'bg-green-400' },
                { label: '激活', value: emotion.arousal, color: 'bg-yellow-400' },
                { label: '好奇', value: emotion.curiosity, color: 'bg-purple-400' },
                { label: '自信', value: emotion.confidence, color: 'bg-blue-400' },
                { label: '投入', value: emotion.engagement, color: 'bg-orange-400' },
              ].map((bar) => (
                <div key={bar.label} className="flex items-center gap-1.5 text-xs">
                  <span className="w-8 text-muted-foreground font-mono text-[10px]">{bar.label}</span>
                  <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full transition-all duration-700', bar.color)}
                      style={{ width: `${Math.round(Math.max(0, Math.min(1, (bar.value + 1) / 2)) * 100)}%` }}
                    />
                  </div>
                  <span className="w-6 text-right font-mono text-muted-foreground text-[10px]">{bar.value.toFixed(1)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Inner Voice Stats */}
          <div className="space-y-1">
            <div className="flex items-center gap-1.5">
              <Sparkles size={12} className="text-yellow-400" />
              <span className="text-xs font-mono text-muted-foreground">内心独白</span>
            </div>
            <div className="grid grid-cols-3 gap-1 text-[10px] font-mono text-center">
              <div className="bg-muted/50 rounded p-1">
                <div className="text-foreground font-bold">{inner_voice.think_count}</div>
                <div className="text-muted-foreground">思考</div>
              </div>
              <div className="bg-muted/50 rounded p-1">
                <div className="text-foreground font-bold">{inner_voice.total_thoughts}</div>
                <div className="text-muted-foreground">想法</div>
              </div>
              <div className="bg-muted/50 rounded p-1">
                <div className="text-foreground font-bold">{inner_voice.expressed_thoughts}</div>
                <div className="text-muted-foreground">表达</div>
              </div>
            </div>
          </div>

          {/* Goals */}
          <GoalTracker />

          {/* World Perception */}
          <div className="space-y-1">
            <div className="flex items-center gap-1.5">
              <Globe size={12} className="text-cyan-400" />
              <span className="text-xs font-mono text-muted-foreground">世界感知</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {[
                { label: '天气', active: world_model.has_weather },
                { label: '新闻', active: world_model.has_news },
                { label: '股市', active: world_model.has_market },
                { label: '加密', active: world_model.has_crypto },
              ].map((item) => (
                <span
                  key={item.label}
                  className={cn(
                    'text-[10px] font-mono px-1.5 py-0.5 rounded',
                    item.active
                      ? 'bg-primary/10 text-primary border border-primary/30'
                      : 'bg-muted/30 text-muted-foreground'
                  )}
                >
                  {item.active ? '✓' : '✗'} {item.label}
                </span>
              ))}
            </div>
          </div>

          {/* Personality Engine Stats */}
          <div className="grid grid-cols-2 gap-1 text-[10px] font-mono">
            <div className="bg-muted/30 rounded p-1.5 flex items-center gap-1.5">
              <Shield size={10} className="text-green-400 flex-shrink-0" />
              <div>
                <div className="text-muted-foreground">一致性</div>
                <div className="text-foreground">
                  {consistency ? `${consistency.current_scene} T${consistency.turn_count}` : '—'}
                </div>
              </div>
            </div>
            <div className="bg-muted/30 rounded p-1.5 flex items-center gap-1.5">
              <Users size={10} className="text-blue-400 flex-shrink-0" />
              <div>
                <div className="text-muted-foreground">反思</div>
                <div className="text-foreground">
                  {self_model.total_conversations}次对话 / {self_model.total_reflections}次反思
                </div>
              </div>
            </div>
          </div>
        </>
      ) : (
        /* Opinions Tab */
        <OpinionList />
      )}
    </div>
  )
}
