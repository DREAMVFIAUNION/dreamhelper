'use client'

import { useState, useCallback, useRef, type DragEvent, type ChangeEvent } from 'react'
import { Upload, FileText, X, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

const ACCEPTED_TYPES = [
  'text/plain',
  'text/markdown',
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]

const ACCEPTED_EXTENSIONS = ['.txt', '.md', '.pdf', '.docx']
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB

interface FileDropZoneProps {
  onUploadComplete?: () => void
}

export function FileDropZone({ onUploadComplete }: FileDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const validateFile = useCallback((f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase()
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      return `不支持的文件类型: ${ext}。支持: ${ACCEPTED_EXTENSIONS.join(', ')}`
    }
    if (f.size > MAX_FILE_SIZE) {
      return `文件过大 (${(f.size / 1024 / 1024).toFixed(1)} MB)，最大 10 MB`
    }
    return null
  }, [])

  const handleFile = useCallback((f: File) => {
    setError(null)
    const err = validateFile(f)
    if (err) {
      setError(err)
      return
    }
    setFile(f)
  }, [validateFile])

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [handleFile])

  const handleChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) handleFile(f)
  }, [handleFile])

  const handleUpload = useCallback(async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    setProgress(10)

    try {
      const formData = new FormData()
      formData.append('file', file)

      setProgress(30)
      const res = await fetch('/api/knowledge/upload', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      setProgress(70)
      const data = await res.json() as { success: boolean; error?: string }

      if (!data.success) {
        throw new Error(data.error || '上传失败')
      }

      setProgress(100)

      // 触发 RAG 索引
      try {
        await fetch('/api/knowledge/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ triggerIndex: true }),
        })
      } catch {
        // RAG indexing is best-effort
      }

      setFile(null)
      setProgress(0)
      onUploadComplete?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : '上传失败')
      setProgress(0)
    } finally {
      setUploading(false)
    }
  }, [file, onUploadComplete])

  const handleClear = useCallback(() => {
    setFile(null)
    setError(null)
    setProgress(0)
    if (inputRef.current) inputRef.current.value = ''
  }, [])

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          'relative border-2 border-dashed p-8 text-center cursor-pointer transition-all',
          isDragging
            ? 'border-primary bg-primary/5'
            : file
              ? 'border-emerald-500/40 bg-emerald-500/5'
              : 'border-border hover:border-primary/30',
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(',')}
          onChange={handleChange}
          className="hidden"
        />

        {file ? (
          <div className="flex items-center justify-center gap-3">
            <FileText size={20} className="text-emerald-400" />
            <div className="text-left">
              <p className="text-xs font-mono font-bold text-foreground">{file.name}</p>
              <p className="text-[10px] font-mono text-muted-foreground">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); handleClear() }}
              className="p-1 text-muted-foreground hover:text-primary transition-colors"
            >
              <X size={14} />
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload size={24} className={cn('mx-auto', isDragging ? 'text-primary' : 'text-muted-foreground/30')} />
            <p className="text-xs font-mono text-muted-foreground">
              拖拽文件到此处，或点击选择
            </p>
            <p className="text-[10px] font-mono text-muted-foreground/50">
              支持 TXT · MD · PDF · DOCX（最大 10 MB）
            </p>
          </div>
        )}

        {/* Progress bar */}
        {uploading && progress > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-secondary">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 px-3 py-2 bg-destructive/5 border border-destructive/20 text-[10px] font-mono text-destructive">
          <AlertCircle size={12} />
          {error}
        </div>
      )}

      {/* Upload button */}
      {file && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="w-full flex items-center justify-center gap-1.5 px-3 py-2 bg-primary/10 border border-primary/30 text-primary text-xs font-mono font-bold hover:bg-primary/20 transition-colors disabled:opacity-50 rounded-md"
        >
          {uploading ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} />}
          {uploading ? '上传中...' : '上传文件'}
        </button>
      )}
    </div>
  )
}
