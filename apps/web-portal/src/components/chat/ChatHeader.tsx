'use client'

import { memo } from 'react'
import { useTranslations } from 'next-intl'
import { PanelLeftClose, PanelLeft, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

interface ChatHeaderProps {
  title: string
  sidebarOpen: boolean
  skillPanelOpen: boolean
  isStreaming: boolean
  messagesLoading: boolean
  onToggleSidebar: () => void
  onToggleSkillPanel: () => void
}

export const ChatHeader = memo(function ChatHeader({
  title,
  sidebarOpen,
  skillPanelOpen,
  isStreaming,
  messagesLoading,
  onToggleSidebar,
  onToggleSkillPanel,
}: ChatHeaderProps) {
  const t = useTranslations('chat')
  return (
    <div className="flex items-center gap-3 px-4 py-3 border-b border-border flex-shrink-0">
      <TooltipProvider delayDuration={0}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={onToggleSidebar}
              className="text-muted-foreground hover:text-primary"
            >
              {sidebarOpen ? <PanelLeftClose size={16} /> : <PanelLeft size={16} />}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">{sidebarOpen ? t('collapseSidebar') : t('expandSidebar')}</TooltipContent>
        </Tooltip>
      </TooltipProvider>
      <div className="w-1 h-6 bg-primary rounded-full shadow-[0_0_6px_hsl(var(--primary)/0.4)]" />
      <div className="flex-1 min-w-0">
        <h1 className="font-display text-sm font-bold text-foreground tracking-wider truncate">
          {title}
        </h1>
        <p className="text-[10px] font-mono text-muted-foreground">
          梦帮小助 · 三脑融合
        </p>
      </div>
      <Button
        variant="ghost"
        size="icon-xs"
        onClick={onToggleSkillPanel}
        aria-label={skillPanelOpen ? '关闭技能面板' : '打开技能面板'}
        className={cn(skillPanelOpen ? 'text-amber-400' : 'text-muted-foreground hover:text-amber-400')}
      >
        <Zap size={14} />
      </Button>
      <Badge variant={isStreaming ? 'warning' : 'success'} className="text-[9px] font-mono px-1.5 py-0 h-5 gap-1">
        <div className={cn('w-1.5 h-1.5 rounded-full', isStreaming ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400')} />
        {isStreaming ? t('generating') : messagesLoading ? t('loading') : t('ready')}
      </Badge>
    </div>
  )
})
