'use client'

import { memo, useState, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { Brain, Bot, User, ChevronDown, Copy, Check, Volume2, VolumeX } from 'lucide-react'
import { cn } from '@/lib/utils'
import { fixStreamingMarkdown } from '@/lib/markdown-stream-fix'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { MarkdownContent } from '@/components/chat/MarkdownContent'
import { ToolCallBlock } from '@/components/chat/ToolCallBlock'
import { RagSources } from '@/components/chat/RagSources'
import type { ToolStep, RagSource, BrainInfo, BrainPhase } from '@/hooks/useStreamChat'

const BrainVisualizer = dynamic(() => import('@/components/chat/BrainVisualizer'), { ssr: false })

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking?: string
}

interface ChatMessageBubbleProps {
  msg: Message
  isLast: boolean
  isStreaming: boolean
  streamContent: string
  streamThinking: string
  toolSteps: ToolStep[]
  agentInfo: { agent: string; description?: string } | null
  ragSources: RagSource[]
  brainInfo: BrainInfo | null
  brainPhase: BrainPhase
  isSpeaking: boolean
  onSpeak: (text: string) => void
  onStopSpeaking: () => void
}

export const ChatMessageBubble = memo(function ChatMessageBubble({
  msg,
  isLast,
  isStreaming,
  streamContent,
  streamThinking,
  toolSteps,
  agentInfo,
  ragSources,
  brainInfo,
  brainPhase,
  isSpeaking,
  onSpeak,
  onStopSpeaking,
}: ChatMessageBubbleProps) {
  const [showThinking, setShowThinking] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const isAssistantStreaming = isLast && msg.role === 'assistant' && isStreaming
  const displayContent = isAssistantStreaming ? fixStreamingMarkdown(streamContent) : msg.content
  const displayThinking = isAssistantStreaming ? streamThinking : msg.thinking

  const handleCopy = useCallback(() => {
    void navigator.clipboard.writeText(displayContent)
    setCopiedId(msg.id)
    setTimeout(() => setCopiedId(null), 2000)
  }, [displayContent, msg.id])

  return (
    <div className={cn('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
      {msg.role === 'assistant' && (
        <div className="flex flex-col items-center gap-1 flex-shrink-0 mt-0.5">
          <div className="w-7 h-7 rounded-md bg-card border border-primary/20 flex items-center justify-center shadow-[0_0_6px_hsl(var(--primary)/0.1)]">
            <Bot size={14} className="text-primary" />
          </div>
          {isAssistantStreaming && agentInfo && agentInfo.agent !== 'react_agent' && (
            <Badge variant="info" className="text-[7px] px-1 py-0 h-3.5">
              {agentInfo.agent.replace('_agent', '').toUpperCase()}
            </Badge>
          )}
        </div>
      )}

      <div className={cn('max-w-[90%] sm:max-w-[75%] space-y-1', msg.role === 'user' ? 'items-end' : 'items-start')}>
        {/* Thinking 折叠块 */}
        {displayThinking && (
          <div className="w-full">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowThinking((s) => !s)}
              className="h-6 px-2 gap-1.5 text-[10px] font-mono text-amber-400/80 hover:text-amber-400 mb-1"
            >
              <Brain size={10} />
              <span>THINKING PROCESS</span>
              <ChevronDown size={10} className={cn('transition-transform', showThinking && 'rotate-180')} />
            </Button>
            {showThinking && (
              <div className="bg-background/50 border border-amber-500/20 rounded-md px-3 py-2 mb-2 text-xs font-mono text-amber-400/70 whitespace-pre-wrap max-h-40 overflow-y-auto scrollbar-none">
                {displayThinking}
              </div>
            )}
          </div>
        )}

        {/* 双脑可视化 */}
        {isAssistantStreaming && brainInfo && brainPhase !== 'idle' && (
          <BrainVisualizer brainInfo={brainInfo} brainPhase={brainPhase} />
        )}

        {/* Agent 工具调用步骤 */}
        {isAssistantStreaming && toolSteps.length > 0 && (
          <ToolCallBlock steps={toolSteps} />
        )}

        {/* 消息内容 */}
        <div
          className={cn(
            'px-3.5 py-2.5 text-sm leading-relaxed rounded-lg',
            msg.role === 'user'
              ? 'bg-primary/10 border border-primary/25 text-foreground'
              : 'bg-card border border-border text-foreground',
          )}
        >
          {!displayContent && isAssistantStreaming ? (
            <span className="inline-flex gap-1">
              <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
              <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse [animation-delay:0.2s]" />
              <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse [animation-delay:0.4s]" />
            </span>
          ) : displayContent ? (
            <>
              <MarkdownContent content={displayContent} />
              {isAssistantStreaming && (
                <span className="inline-block w-0.5 h-4 bg-primary ml-0.5 animate-pulse align-text-bottom" />
              )}
            </>
          ) : null}
        </div>

        {/* RAG 引用来源 */}
        {msg.role === 'assistant' && !isAssistantStreaming && ragSources.length > 0 && isLast && (
          <RagSources sources={ragSources} />
        )}

        {/* 操作按钮: 复制 + TTS */}
        {msg.role === 'assistant' && displayContent && !isAssistantStreaming && (
          <div className="mt-1 flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={handleCopy}
              className="text-muted-foreground/50 hover:text-primary"
            >
              {copiedId === msg.id ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
            </Button>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => isSpeaking ? onStopSpeaking() : onSpeak(displayContent)}
              className="text-muted-foreground/50 hover:text-primary"
            >
              {isSpeaking ? <VolumeX size={12} /> : <Volume2 size={12} />}
            </Button>
          </div>
        )}
      </div>

      {msg.role === 'user' && (
        <div className="w-7 h-7 rounded-md bg-primary/15 border border-primary/30 flex items-center justify-center flex-shrink-0 mt-0.5">
          <User size={14} className="text-primary" />
        </div>
      )}
    </div>
  )
})
