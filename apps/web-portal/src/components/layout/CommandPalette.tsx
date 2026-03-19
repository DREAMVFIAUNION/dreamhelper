'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  MessageSquare, LayoutDashboard, Settings, BookOpen, Zap,
  BarChart3, Bot, Workflow, Search,
} from 'lucide-react'
import {
  CommandDialog, CommandInput, CommandList, CommandEmpty,
  CommandGroup, CommandItem, CommandSeparator,
} from '@/components/ui/command'

const NAV_ITEMS = [
  { label: '对话', icon: MessageSquare, href: '/chat', group: '导航' },
  { label: '总览', icon: LayoutDashboard, href: '/overview', group: '导航' },
  { label: '知识库', icon: BookOpen, href: '/knowledge', group: '导航' },
  { label: '智能体', icon: Bot, href: '/agents', group: '导航' },
  { label: '工作流', icon: Workflow, href: '/workflows', group: '导航' },
  { label: '数据分析', icon: BarChart3, href: '/analytics', group: '导航' },
  { label: '设置', icon: Settings, href: '/settings', group: '导航' },
]

const QUICK_ACTIONS = [
  { label: '新建对话', icon: MessageSquare, href: '/chat', group: '快捷操作' },
  { label: '搜索知识库', icon: Search, href: '/knowledge', group: '快捷操作' },
  { label: '创建工作流', icon: Workflow, href: '/workflows', group: '快捷操作' },
]

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((o) => !o)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const runCommand = useCallback((command: () => void) => {
    setOpen(false)
    command()
  }, [])

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="搜索页面或操作... (Ctrl+K)" />
      <CommandList>
        <CommandEmpty className="text-xs font-mono text-muted-foreground">
          未找到结果
        </CommandEmpty>
        <CommandGroup heading="导航">
          {NAV_ITEMS.map((item) => (
            <CommandItem
              key={item.href}
              onSelect={() => runCommand(() => router.push(item.href))}
              className="gap-2 text-xs font-mono"
            >
              <item.icon size={14} className="text-muted-foreground" />
              <span>{item.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="快捷操作">
          {QUICK_ACTIONS.map((item) => (
            <CommandItem
              key={item.label}
              onSelect={() => runCommand(() => router.push(item.href))}
              className="gap-2 text-xs font-mono"
            >
              <item.icon size={14} className="text-primary" />
              <span>{item.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
