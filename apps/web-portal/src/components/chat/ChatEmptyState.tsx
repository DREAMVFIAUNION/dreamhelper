'use client'

import { memo } from 'react'
import { useTranslations } from 'next-intl'
import { Bot } from 'lucide-react'

interface ChatEmptyStateProps {
  onSelectSuggestion: (text: string) => void
}

export const ChatEmptyState = memo(function ChatEmptyState({ onSelectSuggestion }: ChatEmptyStateProps) {
  const t = useTranslations('chat')

  const suggestions = [
    { icon: '💡', text: t('suggestions.s1') },
    { icon: '📝', text: t('suggestions.s2') },
    { icon: '🔍', text: t('suggestions.s3') },
    { icon: '🧮', text: t('suggestions.s4') },
  ]

  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <div className="w-16 h-16 rounded-xl bg-card border border-border flex items-center justify-center mb-4 shadow-[0_0_20px_hsl(var(--primary)/0.1)]">
        <Bot size={28} className="text-primary drop-shadow-[0_0_8px_hsl(var(--primary)/0.4)]" />
      </div>
      <h2 className="font-display text-lg font-bold text-foreground tracking-wider mb-1">{t('emptyTitle')}</h2>
      <p className="text-xs font-mono text-muted-foreground max-w-sm">
        {t('emptyDesc')} · Triple-Brain
      </p>
      <p className="text-sm text-secondary-foreground mt-3 mb-5">{t('emptyHint')}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-md w-full">
        {suggestions.map((chip) => (
          <button
            key={chip.text}
            onClick={() => onSelectSuggestion(chip.text)}
            className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-card border border-border text-left hover:border-primary/30 hover:shadow-[0_0_10px_hsl(var(--primary)/0.06)] transition-all group"
          >
            <span className="text-base">{chip.icon}</span>
            <span className="text-xs font-mono text-muted-foreground group-hover:text-foreground transition-colors truncate">{chip.text}</span>
          </button>
        ))}
      </div>
    </div>
  )
})
