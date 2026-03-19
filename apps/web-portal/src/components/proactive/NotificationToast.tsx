'use client'

import { X, Bell } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface NotificationMessage {
  type: string
  title: string
  content: string
  timestamp?: number
}

interface Props {
  messages: NotificationMessage[]
  onDismiss: (index: number) => void
  onDismissAll: () => void
}

export function NotificationToast({ messages, onDismiss, onDismissAll }: Props) {
  if (messages.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {messages.map((msg, i) => (
        <div
          key={`${msg.type}-${msg.timestamp ?? i}-${i}`}
          className={cn(
            'bg-card border border-primary/30 rounded px-4 py-3',
            'shadow-[0_0_20px_rgba(254,0,0,0.15)]',
            'animate-in slide-in-from-right duration-300',
          )}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 text-xs font-mono text-primary font-bold">
              <Bell size={12} />
              {msg.title}
            </div>
            <button
              onClick={() => onDismiss(i)}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <X size={14} />
            </button>
          </div>
          <p className="mt-1.5 text-sm text-foreground leading-relaxed">
            {msg.content}
          </p>
        </div>
      ))}
      {messages.length > 1 && (
        <button
          onClick={onDismissAll}
          className="text-[10px] font-mono text-muted-foreground hover:text-primary transition-colors text-right"
        >
          DISMISS ALL
        </button>
      )}
    </div>
  )
}
