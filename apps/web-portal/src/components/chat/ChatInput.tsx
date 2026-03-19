'use client'

import { memo, useRef, useCallback, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { Send, Square, Mic, MicOff, Loader2, Paperclip, X, FileText, FileSpreadsheet, FileCode } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import type { FileAttachment } from '@/hooks/useFileUpload'

const DOC_ICONS: Record<string, typeof FileText> = {
  '.pdf': FileText,
  '.docx': FileText,
  '.xlsx': FileSpreadsheet,
  '.csv': FileSpreadsheet,
  '.json': FileCode,
  '.md': FileCode,
  '.txt': FileText,
}

interface ChatInputProps {
  input: string
  isStreaming: boolean
  isRecording: boolean
  isTranscribing: boolean
  images?: FileAttachment[]
  documents?: FileAttachment[]
  imageUploading?: boolean
  isDocParsing?: boolean
  acceptTypes?: string
  onInputChange: (value: string) => void
  onSend: () => void
  onAbort: () => void
  onStartRecording: () => void
  onStopRecording: () => void
  onOpenFilePicker?: () => void
  onRemoveImage?: (id: string) => void
  onPaste?: (e: React.ClipboardEvent) => void
  fileInputRef?: React.RefObject<HTMLInputElement | null>
  onFileChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export const ChatInput = memo(function ChatInput({
  input,
  isStreaming,
  isRecording,
  isTranscribing,
  images = [],
  documents = [],
  imageUploading = false,
  isDocParsing = false,
  acceptTypes,
  onInputChange,
  onSend,
  onAbort,
  onStartRecording,
  onStopRecording,
  onOpenFilePicker,
  onRemoveImage,
  onPaste,
  fileInputRef,
  onFileChange,
}: ChatInputProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const t = useTranslations('chat')
  const canSend = (input.trim() || images.length > 0 || documents.length > 0) && !isDocParsing

  // textarea 自动扩展 (最多 8 行)
  useEffect(() => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 192) + 'px' // 192px ≈ 8 行
  }, [input])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }, [onSend])

  return (
    <div className="border-t border-border px-3 sm:px-6 py-3 flex-shrink-0">
      {/* 附件预览条 */}
      {(images.length > 0 || documents.length > 0) && (
        <div className="flex gap-2 mb-2 flex-wrap">
          {/* 图片预览 */}
          {images.map((img) => (
            <div key={img.id} className="relative group w-16 h-16 rounded-md overflow-hidden border border-border bg-secondary">
              <img src={img.previewUrl} alt="" className="w-full h-full object-cover" />
              {onRemoveImage && (
                <button
                  onClick={() => onRemoveImage(img.id)}
                  className="absolute top-0.5 right-0.5 w-4 h-4 bg-black/60 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label={t('removeImage')}
                >
                  <X size={10} className="text-white" />
                </button>
              )}
            </div>
          ))}
          {/* 文档预览 */}
          {documents.map((doc) => {
            const Icon = DOC_ICONS[doc.ext] || FileText
            return (
              <div key={doc.id} className="relative group flex items-center gap-1.5 px-2 py-1.5 rounded-md border border-border bg-secondary max-w-[200px]">
                <Icon size={14} className={cn(
                  doc.parsing ? 'text-amber-400 animate-pulse' : doc.parseError ? 'text-destructive' : 'text-emerald-400',
                )} />
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] font-mono font-bold text-foreground truncate">{doc.file.name}</div>
                  <div className="text-[8px] font-mono text-muted-foreground">
                    {doc.parsing ? '解析中...' : doc.parseError ? '解析失败' : `${(doc.file.size / 1024).toFixed(0)}KB ✓`}
                  </div>
                </div>
                {onRemoveImage && (
                  <button
                    onClick={() => onRemoveImage(doc.id)}
                    className="w-4 h-4 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-primary"
                  >
                    <X size={10} />
                  </button>
                )}
              </div>
            )
          })}
          {(imageUploading || isDocParsing) && (
            <div className="w-16 h-16 rounded-md border border-border bg-secondary flex items-center justify-center">
              <Loader2 size={14} className="animate-spin text-muted-foreground" />
            </div>
          )}
        </div>
      )}

      <div className="flex items-end gap-1 bg-card border border-border rounded-lg">
        {/* 附件上传按钮 */}
        {onOpenFilePicker && (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onOpenFilePicker}
            disabled={isStreaming || imageUploading || isDocParsing}
            aria-label={t('uploadImage')}
            className="text-muted-foreground/60 hover:text-primary"
            title="上传图片或文档 (PDF/DOCX/XLSX/TXT/MD/CSV)"
          >
            <Paperclip size={15} />
          </Button>
        )}

        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={onPaste}
          placeholder={t('placeholder')}
          rows={1}
          aria-label={t('title')}
          className="flex-1 bg-transparent px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/50 outline-none resize-none font-mono max-h-32"
          disabled={isStreaming}
        />
        {/* 语音输入 */}
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={isRecording ? onStopRecording : onStartRecording}
          disabled={isStreaming || isTranscribing}
          aria-label={isRecording ? t('stopRecording') : t('startRecording')}
          className={cn(
            isRecording ? 'text-primary animate-pulse' : 'text-muted-foreground/60 hover:text-primary',
          )}
        >
          {isTranscribing ? <Loader2 size={15} className="animate-spin" /> : isRecording ? <MicOff size={15} /> : <Mic size={15} />}
        </Button>

        {isStreaming ? (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onAbort}
            aria-label={t('stopGenerating')}
            className="text-amber-400 hover:text-amber-300"
          >
            <Square size={16} />
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onSend}
            disabled={!canSend}
            aria-label={t('send')}
            className={cn(
              canSend ? 'text-primary hover:text-primary/80' : 'text-muted-foreground/30',
            )}
          >
            <Send size={16} />
          </Button>
        )}
      </div>

      {/* 隐藏的文件输入 */}
      {fileInputRef && onFileChange && (
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptTypes || "image/jpeg,image/png,image/gif,image/webp,image/bmp,.pdf,.docx,.xlsx,.txt,.md,.csv,.json"}
          multiple
          onChange={onFileChange}
          className="hidden"
        />
      )}
      <div className="flex items-center justify-between mt-1.5 px-1">
        <span className="text-[9px] font-mono text-muted-foreground/40">{t('footer1')}</span>
        <span className="text-[9px] font-mono text-muted-foreground/40">{t('footer2')}</span>
      </div>
    </div>
  )
})
