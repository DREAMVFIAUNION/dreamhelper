'use client'

import { cn } from '@/lib/utils'
import { Lightbulb, Brain, Heart, Globe, HelpCircle } from 'lucide-react'

export interface ThoughtMessage {
  type: string
  title: string
  content: string
  topic?: string
  timestamp?: number
}

interface Props {
  message: ThoughtMessage
  onReply?: (content: string) => void
}

const TOPIC_ICONS: Record<string, React.ReactNode> = {
  tech: <Lightbulb size={14} className="text-yellow-400" />,
  ai: <Brain size={14} className="text-purple-400" />,
  user_care: <Heart size={14} className="text-pink-400" />,
  self_reflect: <Brain size={14} className="text-cyan-400" />,
  world: <Globe size={14} className="text-green-400" />,
  curiosity: <Lightbulb size={14} className="text-orange-400" />,
  question: <HelpCircle size={14} className="text-blue-400" />,
}

export function ThoughtBubble({ message, onReply }: Props) {
  const icon = TOPIC_ICONS[message.topic || ''] || <Brain size={14} className="text-primary" />
  const time = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    : ''

  return (
    <div className="flex justify-start mb-4">
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-3',
          'border border-dashed border-primary/40',
          'bg-primary/5',
          'shadow-[0_0_12px_rgba(254,0,0,0.08)]',
        )}
      >
        {/* Header */}
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-lg">💭</span>
          {icon}
          <span className="text-xs font-mono font-bold text-primary/80">
            {message.title || '小助想说'}
          </span>
          {time && (
            <span className="text-[10px] font-mono text-muted-foreground ml-auto">
              {time}
            </span>
          )}
        </div>

        {/* Content */}
        <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>

        {/* Reply hint */}
        {onReply && (
          <div className="mt-2 pt-1.5 border-t border-dashed border-primary/20">
            <span className="text-[10px] font-mono text-muted-foreground">
              可以直接回复继续对话
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
