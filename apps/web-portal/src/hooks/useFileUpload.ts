'use client'

import { useState, useCallback, useRef } from 'react'

// ── 附件类型 ──────────────────────────────────────────────
export type AttachmentKind = 'image' | 'document'

export interface FileAttachment {
  id: string
  kind: AttachmentKind
  file: File
  previewUrl: string          // 图片: blob URL; 文档: ''
  ext: string                 // '.pdf', '.docx', '.png' ...
  parsedText?: string         // 文档解析后的文本内容
  parsing?: boolean           // 是否正在解析
  parseError?: string         // 解析错误信息
}

// 向后兼容旧接口
export type ImageAttachment = FileAttachment

// ── 常量 ──────────────────────────────────────────────────
const MAX_SIZE = 20 * 1024 * 1024 // 20MB

const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']

const DOCUMENT_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',   // .docx
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',         // .xlsx
  'text/plain',
  'text/markdown',
  'text/csv',
  'application/json',
]

const DOCUMENT_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.txt', '.md', '.csv', '.json']

const ALL_ACCEPT = [
  ...IMAGE_TYPES,
  ...DOCUMENT_EXTENSIONS.map(e => e),  // 用扩展名兜底
  ...DOCUMENT_TYPES,
].join(',')

// ── 工具函数 ──────────────────────────────────────────────
function getExt(name: string): string {
  const parts = name.split('.')
  return parts.length > 1 ? '.' + parts.pop()!.toLowerCase() : ''
}

function classifyFile(file: File): AttachmentKind | null {
  if (IMAGE_TYPES.includes(file.type)) return 'image'
  if (DOCUMENT_TYPES.includes(file.type)) return 'document'
  const ext = getExt(file.name)
  if (DOCUMENT_EXTENSIONS.includes(ext)) return 'document'
  return null
}

function genId(): string {
  return typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2) + Date.now().toString(36)
}

// ── 文档内容截断 ─────────────────────────────────────────
const MAX_DOC_CHARS = 8000

function truncateDocText(text: string, fileName: string): string {
  if (text.length <= MAX_DOC_CHARS) return text
  return text.slice(0, MAX_DOC_CHARS) + `\n\n⚠️ 文档较长，已截取前 ${MAX_DOC_CHARS} 字（原文 ${text.length} 字）`
}

// ── Hook ──────────────────────────────────────────────────
export function useFileUpload() {
  const [files, setFiles] = useState<FileAttachment[]>([])
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef<HTMLInputElement | null>(null)

  // ── 添加文件 ──
  const addFile = useCallback((file: File): string | null => {
    const kind = classifyFile(file)
    if (!kind) {
      return `不支持的文件类型: ${file.type || getExt(file.name)}。支持图片和文档（PDF/DOCX/XLSX/TXT/MD/CSV）`
    }
    if (file.size > MAX_SIZE) {
      return `文件过大 (${(file.size / 1024 / 1024).toFixed(1)}MB)，最大 ${MAX_SIZE / 1024 / 1024}MB`
    }
    const id = genId()
    const ext = getExt(file.name)
    const previewUrl = kind === 'image' ? URL.createObjectURL(file) : ''

    const attachment: FileAttachment = { id, kind, file, previewUrl, ext }
    setFiles((prev) => [...prev, attachment])

    // 文档自动解析
    if (kind === 'document') {
      void parseDocument(id, file)
    }

    return null
  }, [])

  // ── 文档解析 ──
  const parseDocument = useCallback(async (id: string, file: File) => {
    setFiles((prev) => prev.map(f => f.id === id ? { ...f, parsing: true } : f))

    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch('/api/multimodal/document', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })
      const data = await res.json() as { success: boolean; text?: string; error?: string }

      if (data.success && data.text) {
        const truncated = truncateDocText(data.text, file.name)
        setFiles((prev) => prev.map(f => f.id === id ? { ...f, parsing: false, parsedText: truncated } : f))
      } else {
        setFiles((prev) => prev.map(f => f.id === id ? { ...f, parsing: false, parseError: data.error || '解析失败' } : f))
      }
    } catch {
      setFiles((prev) => prev.map(f => f.id === id ? { ...f, parsing: false, parseError: '文档解析服务不可用' } : f))
    }
  }, [])

  // ── 移除文件 ──
  const removeFile = useCallback((id: string) => {
    setFiles((prev) => {
      const f = prev.find(i => i.id === id)
      if (f?.previewUrl) URL.revokeObjectURL(f.previewUrl)
      return prev.filter(i => i.id !== id)
    })
  }, [])

  // ── 清空所有 ──
  const clearFiles = useCallback(() => {
    setFiles((prev) => {
      prev.forEach(i => { if (i.previewUrl) URL.revokeObjectURL(i.previewUrl) })
      return []
    })
  }, [])

  // ── 打开选择器 ──
  const openFilePicker = useCallback(() => {
    inputRef.current?.click()
  }, [])

  // ── onChange ──
  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const fileList = e.target.files
      if (!fileList) return
      for (let i = 0; i < fileList.length; i++) {
        const err = addFile(fileList[i]!)
        if (err) console.warn('[FileUpload]', err)
      }
      e.target.value = ''
    },
    [addFile],
  )

  // ── 粘贴 ──
  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      const items = e.clipboardData?.items
      if (!items) return
      for (let i = 0; i < items.length; i++) {
        const item = items[i]!
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile()
          if (file) {
            e.preventDefault()
            addFile(file)
          }
        }
      }
    },
    [addFile],
  )

  // ── 分析图片 (Vision API) ──
  const analyzeImages = useCallback(async (userQuestion?: string): Promise<string> => {
    const imageFiles = files.filter(f => f.kind === 'image')
    if (imageFiles.length === 0) return ''
    setUploading(true)
    const results: string[] = []
    try {
      for (const img of imageFiles) {
        const formData = new FormData()
        formData.append('image', img.file)
        formData.append('question', userQuestion || '请详细描述这张图片的内容，包括场景、物体、文字、颜色等。')
        try {
          const res = await fetch('/api/multimodal/vision', {
            method: 'POST',
            credentials: 'include',
            body: formData,
          })
          const data = await res.json() as { description?: string; analysis?: string; error?: string; model?: string }
          if (data.description || data.analysis) {
            const model = data.model ? ` (${data.model})` : ''
            results.push(`[视觉感知] 我通过视觉皮层${model}看到了图片「${img.file.name}」：\n\n${data.description || data.analysis || ''}`)
          } else if (data.error) {
            results.push(`[视觉感知] 图片「${img.file.name}」视觉分析失败: ${data.error}`)
          }
        } catch {
          results.push(`[视觉感知] 图片「${img.file.name}」视觉服务暂不可用`)
        }
      }
    } finally {
      setUploading(false)
    }
    return results.join('\n\n')
  }, [files])

  // ── 获取文档解析文本 ──
  const getDocumentTexts = useCallback((): string => {
    const docs = files.filter(f => f.kind === 'document' && f.parsedText)
    if (docs.length === 0) return ''
    return docs.map(d => `[文档内容] 我阅读了用户上传的文档「${d.file.name}」(${(d.file.size / 1024).toFixed(1)}KB)：\n\n${d.parsedText}`).join('\n\n---\n\n')
  }, [files])

  // ── 向后兼容: images 只包含图片附件 ──
  const images = files.filter(f => f.kind === 'image')
  const documents = files.filter(f => f.kind === 'document')
  const hasFiles = files.length > 0
  const hasImages = images.length > 0
  const hasDocuments = documents.length > 0
  const isDocParsing = documents.some(d => d.parsing)

  return {
    files,
    images,              // 向后兼容
    documents,
    uploading,
    inputRef,
    addFile,
    addImage: addFile,   // 向后兼容
    removeFile,
    removeImage: removeFile, // 向后兼容
    clearFiles,
    clearImages: clearFiles, // 向后兼容
    openFilePicker,
    handleFileChange,
    handlePaste,
    analyzeImages,
    getDocumentTexts,
    hasFiles,
    hasImages,
    hasDocuments,
    isDocParsing,
    acceptTypes: ALL_ACCEPT,
  }
}

// 向后兼容: 保持 useImageUpload 导出名
export const useImageUpload = useFileUpload
