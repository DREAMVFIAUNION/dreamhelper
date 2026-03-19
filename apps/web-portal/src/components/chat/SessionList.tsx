'use client'

import { useState } from 'react'
import { Plus, Trash2, Pencil, Check, X, MessageSquare, Loader2 } from 'lucide-react'
import type { ChatSessionItem } from '@/hooks/useSessionManager'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader,
  AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction,
} from '@/components/ui/alert-dialog'

interface SessionListProps {
  sessions: ChatSessionItem[]
  currentSessionId: string | null
  loading: boolean
  onSelect: (id: string) => void
  onCreate: () => void
  onDelete: (id: string) => void
  onRename: (id: string, title: string) => void
}

export function SessionList({
  sessions,
  currentSessionId,
  loading,
  onSelect,
  onCreate,
  onDelete,
  onRename,
}: SessionListProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)

  function startRename(session: ChatSessionItem) {
    setEditingId(session.id)
    setEditTitle(session.title)
  }

  function confirmRename() {
    if (editingId && editTitle.trim()) {
      onRename(editingId, editTitle.trim())
    }
    setEditingId(null)
  }

  function cancelRename() {
    setEditingId(null)
  }

  return (
    <div className="w-64 bg-card border-r border-border flex flex-col h-full">
      {/* 顶部: 新建对话 */}
      <div className="p-3 border-b border-border">
        <button
          onClick={onCreate}
          aria-label="新建对话"
          className="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-primary/10 border border-primary/30 text-primary text-xs font-mono font-bold hover:bg-primary/20 transition-colors rounded-md"
        >
          <Plus size={14} />
          新建对话
        </button>
      </div>

      {/* 会话列表 */}
      <nav aria-label="对话列表" className="flex-1 overflow-y-auto py-1">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={16} className="animate-spin text-muted-foreground" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <MessageSquare size={24} className="mx-auto text-muted-foreground/30 mb-2" />
            <p className="text-[10px] font-mono text-muted-foreground/50">暂无对话</p>
            <p className="text-[10px] font-mono text-muted-foreground/30 mt-0.5">点击上方按钮开始</p>
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === currentSessionId
            const isEditing = session.id === editingId

            return (
              <div
                key={session.id}
                className={cn(
                  'group mx-1 my-0.5 px-3 py-2 rounded cursor-pointer transition-all',
                  isActive
                    ? 'bg-primary/10 border-l-2 border-primary'
                    : 'hover:bg-accent border-l-2 border-transparent',
                )}
                onClick={() => !isEditing && onSelect(session.id)}
              >
                {isEditing ? (
                  <div className="flex items-center gap-1">
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') confirmRename()
                        if (e.key === 'Escape') cancelRename()
                      }}
                      autoFocus
                      className="flex-1 bg-secondary border border-border px-1.5 py-0.5 text-[11px] font-mono text-foreground outline-none focus:border-primary/50"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <button onClick={(e) => { e.stopPropagation(); confirmRename() }} className="p-0.5 text-emerald-400 hover:bg-emerald-400/10 rounded">
                      <Check size={12} />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); cancelRename() }} className="p-0.5 text-muted-foreground hover:bg-accent rounded">
                      <X size={12} />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className={cn(
                        'text-[11px] font-mono truncate',
                        isActive ? 'text-primary' : 'text-foreground',
                      )}>
                        {session.title}
                      </div>
                      <div className="text-[9px] font-mono text-muted-foreground/50 mt-0.5">
                        {session.messageCount} 条消息
                      </div>
                    </div>
                    <div className="hidden group-hover:flex items-center gap-0.5 ml-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); startRename(session) }}
                        className="p-1 text-muted-foreground/50 hover:text-foreground rounded transition-colors"
                        title="重命名"
                        aria-label="重命名对话"
                      >
                        <Pencil size={10} />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); setDeleteTarget(session.id) }}
                        className="p-1 text-muted-foreground/50 hover:text-primary rounded transition-colors"
                        title="删除"
                        aria-label="删除对话"
                      >
                        <Trash2 size={10} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
      </nav>

      {/* 底部信息 */}
      <div className="px-3 py-2 border-t border-border">
        <div className="text-[9px] font-mono text-muted-foreground/40 text-center">
          {sessions.length} 个对话
        </div>
      </div>

      {/* 删除确认对话框 */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent className="max-w-sm">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-sm font-mono">删除对话</AlertDialogTitle>
            <AlertDialogDescription className="text-xs font-mono">
              确定要删除这个对话吗？此操作不可撤销，所有消息记录将被永久删除。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="text-xs font-mono">取消</AlertDialogCancel>
            <AlertDialogAction
              className="text-xs font-mono bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => { if (deleteTarget) onDelete(deleteTarget); setDeleteTarget(null) }}
            >
              删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
