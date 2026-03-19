'use client'

import { type BrainInfo, type BrainPhase } from '@/hooks/useStreamChat'

interface BrainVisualizerProps {
  brainInfo: BrainInfo
  brainPhase: BrainPhase
}

const STRATEGY_LABELS: Record<string, string> = {
  compete: '竞争择优',
  complement: '互补融合',
  debate: '辩论共识',
  weighted: '加权混合',
  single_left: '左脑独立',
  single_right: '右脑独立',
}

const TASK_TYPE_LABELS: Record<string, string> = {
  code: '代码编程',
  writing: '文案写作',
  analysis: '逻辑分析',
  math: '数学计算',
  qa: '事实问答',
  creative: '创意发散',
  chat: '日常对话',
  complex: '复合任务',
}

const COMPLEXITY_LABELS: Record<string, { label: string; color: string }> = {
  simple: { label: '简单', color: '#22c55e' },
  medium: { label: '中等', color: '#eab308' },
  complex: { label: '复杂', color: '#f97316' },
  expert: { label: '专家', color: '#ef4444' },
}

function PhaseIndicator({ phase, mode }: { phase: BrainPhase; mode: 'dual' | 'triple' }) {
  const labels: Record<BrainPhase, string> = {
    idle: '',
    thalamus_routing: '丘脑路由中...',
    thalamus_done: '丘脑路由完成',
    brainstem_responding: '脑干响应中...',
    brainstem_analyzing: '脑干+双脑 并行分析...',
    cortex_activating: '皮层激活中...',
    thinking: '双脑推理中...',
    left_done: '左脑完成，等待右脑...',
    right_done: '右脑完成，等待左脑...',
    brainstem_directive: '脑干指令就绪',
    fusing: '皮层融合中...',
    brainstem_reviewing: '脑干质控中...',
    done: '融合完成',
  }
  if (phase === 'idle') return null
  const isActive = phase !== 'done' && phase !== 'brainstem_directive'
  return (
    <span className={`text-[10px] font-mono ${isActive ? 'text-cyan-400 animate-pulse' : 'text-cyan-500'}`}>
      {labels[phase]}
    </span>
  )
}

function LatencyLabel({ ms }: { ms: number }) {
  if (ms <= 0) return null
  const text = ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(1)}s`
  return <span className="w-14 text-right font-mono text-gray-500 text-[10px]">{text}</span>
}

function WeightBar({ label, weight, latencyMs, isDone, color }: {
  label: string
  weight: number
  latencyMs: number
  isDone: boolean
  color: string
}) {
  const pct = Math.round(weight * 100)
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-8 text-right font-mono text-[10px]" style={{ color }}>{label}</span>
      <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${pct}%`,
            backgroundColor: color,
            opacity: isDone ? 1 : 0.4,
          }}
        />
      </div>
      <span className="w-8 text-right font-mono text-gray-400 text-[10px]">{pct}%</span>
      <LatencyLabel ms={latencyMs} />
    </div>
  )
}

export default function BrainVisualizer({ brainInfo, brainPhase }: BrainVisualizerProps) {
  if (brainPhase === 'idle') return null

  const isTriple = brainInfo.mode === 'triple'
  const taskLabel = TASK_TYPE_LABELS[brainInfo.taskType] || brainInfo.taskType
  const strategyLabel = STRATEGY_LABELS[brainInfo.fusionStrategy] || brainInfo.fusionStrategy
  const complexity = COMPLEXITY_LABELS[brainInfo.brainstemComplexity]
  const hemispheresDone = brainPhase === 'fusing' || brainPhase === 'brainstem_reviewing' || brainPhase === 'done' || brainPhase === 'brainstem_directive'

  return (
    <div className="mb-3 p-3 rounded-lg border border-cyan-900/40 bg-gray-900/60 backdrop-blur-sm space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm">{isTriple ? '🧬' : '🧠'}</span>
          <span className="text-xs font-semibold text-gray-300">
            {isTriple ? '三脑协作' : '双脑协作'}
          </span>
          {taskLabel && (
            <span className="px-1.5 py-0.5 text-[10px] rounded bg-cyan-900/50 text-cyan-300">
              {taskLabel}
            </span>
          )}
          {complexity && (
            <span className="px-1.5 py-0.5 text-[10px] rounded" style={{ backgroundColor: complexity.color + '20', color: complexity.color }}>
              {complexity.label}
            </span>
          )}
        </div>
        <PhaseIndicator phase={brainPhase} mode={isTriple ? 'triple' : 'dual'} />
      </div>

      {/* Brainstem bar (only in triple mode) */}
      {isTriple && (
        <div className="flex items-center gap-2 text-xs">
          <span className="w-8 text-right font-mono text-[10px] text-emerald-400">脑干</span>
          <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700 bg-emerald-500"
              style={{
                width: brainInfo.brainstemLatencyMs > 0 ? '100%' : brainPhase === 'brainstem_analyzing' || brainPhase === 'thinking' ? '60%' : '0%',
                opacity: brainInfo.brainstemLatencyMs > 0 ? 1 : 0.4,
              }}
            />
          </div>
          <span className="w-8 text-right font-mono text-gray-400 text-[10px]">GLM</span>
          <LatencyLabel ms={brainInfo.brainstemLatencyMs} />
        </div>
      )}

      {/* Left/Right weight bars */}
      <div className="space-y-1">
        <WeightBar
          label="左脑"
          weight={brainInfo.weights.left}
          latencyMs={brainInfo.leftLatencyMs}
          isDone={hemispheresDone || brainPhase === 'left_done'}
          color="#06b6d4"
        />
        <WeightBar
          label="右脑"
          weight={brainInfo.weights.right}
          latencyMs={brainInfo.rightLatencyMs}
          isDone={hemispheresDone || brainPhase === 'right_done'}
          color="#a855f7"
        />
      </div>

      {/* Brainstem focus hint */}
      {isTriple && brainInfo.brainstemFocus && hemispheresDone && (
        <div className="text-[10px] text-emerald-400/70 font-mono px-1 truncate">
          📋 {brainInfo.brainstemFocus}
        </div>
      )}

      {/* Footer: strategy + confidence + models */}
      {(brainPhase === 'fusing' || brainPhase === 'brainstem_reviewing' || brainPhase === 'done') && (
        <div className="flex items-center justify-between text-[10px] text-gray-500 pt-1 border-t border-gray-800 flex-wrap gap-y-0.5">
          {strategyLabel && (
            <span>
              ⚡ <span className="text-gray-400">{strategyLabel}</span>
            </span>
          )}
          {brainInfo.confidence > 0 && (
            <span>
              📊 <span className="text-gray-400">{(brainInfo.confidence * 100).toFixed(0)}%</span>
            </span>
          )}
          {brainInfo.qualityScore !== null && (
            <span>
              ✅ <span className="text-gray-400">{brainInfo.qualityScore}/10</span>
            </span>
          )}
          <span className="text-gray-600">
            {brainInfo.leftModel ? brainInfo.leftModel.split('-').pop() : 'L'}
            {' + '}
            {brainInfo.rightModel ? brainInfo.rightModel.split('-').pop() : 'R'}
            {isTriple && ' + GLM'}
          </span>
        </div>
      )}
    </div>
  )
}
