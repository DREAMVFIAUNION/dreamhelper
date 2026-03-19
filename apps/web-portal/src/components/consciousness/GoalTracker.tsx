'use client'

import { useEffect, useState } from 'react'
import { Target, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Goal {
  id: string
  title: string
  goal_type: string
  priority: number
  status: string
  progress: number
}

const STATUS_COLORS: Record<string, string> = {
  active: 'text-green-400',
  paused: 'text-yellow-400',
  completed: 'text-blue-400',
  abandoned: 'text-muted-foreground',
}

const TYPE_LABELS: Record<string, string> = {
  long_term: '长期',
  short_term: '短期',
  autonomous: '自主',
}

export function GoalTracker() {
  const [goals, setGoals] = useState<Goal[]>([])
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    fetch('/api/consciousness/goals')
      .then((r) => r.json())
      .then((data) => {
        if (data.goals) setGoals(data.goals)
      })
      .catch(() => {})
  }, [])

  const active = goals.filter((g) => g.status === 'active')
  const display = expanded ? goals : active.slice(0, 3)

  if (goals.length === 0) {
    return (
      <div className="text-[10px] text-muted-foreground font-mono px-3 py-1">
        暂无目标数据
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Target size={12} className="text-green-400" />
          <span className="text-xs font-mono text-muted-foreground">目标系统</span>
          <span className="text-[10px] font-mono text-muted-foreground ml-1">
            {active.length} 活跃 / {goals.length} 总计
          </span>
        </div>
        {goals.length > 3 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-muted-foreground hover:text-primary transition-colors"
          >
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        )}
      </div>

      <div className="space-y-1.5">
        {display.map((goal) => (
          <div key={goal.id} className="flex items-center gap-2">
            {/* Priority dot */}
            <div
              className={cn(
                'w-1.5 h-1.5 rounded-full flex-shrink-0',
                goal.priority >= 0.8
                  ? 'bg-red-400'
                  : goal.priority >= 0.5
                    ? 'bg-yellow-400'
                    : 'bg-muted-foreground',
              )}
            />
            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1">
                <span className={cn('text-[10px] font-mono', STATUS_COLORS[goal.status] || 'text-foreground')}>
                  {goal.title}
                </span>
                <span className="text-[9px] font-mono text-muted-foreground/60 ml-auto flex-shrink-0">
                  {TYPE_LABELS[goal.goal_type] || goal.goal_type}
                </span>
              </div>
              {/* Progress bar */}
              <div className="w-full h-1 bg-muted/30 rounded-full overflow-hidden mt-0.5">
                <div
                  className={cn(
                    'h-full rounded-full transition-all',
                    goal.status === 'completed' ? 'bg-blue-400' : 'bg-primary/60',
                  )}
                  style={{ width: `${Math.round(goal.progress * 100)}%` }}
                />
              </div>
            </div>
            {/* Progress % */}
            <span className="text-[9px] font-mono text-muted-foreground flex-shrink-0 w-6 text-right">
              {Math.round(goal.progress * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
