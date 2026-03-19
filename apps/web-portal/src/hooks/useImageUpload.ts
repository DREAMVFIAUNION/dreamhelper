'use client'

import { useState, useCallback, useRef } from 'react'

export interface ImageAttachment {
  id: string
  file: File
  previewUrl: string
}

const MAX_SIZE = 10 * 1024 * 1024 // 10MB
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']

export function useImageUpload() {
  const [images, setImages] = useState<ImageAttachment[]>([])
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef<HTMLInputElement | null>(null)

  const addImage = useCallback((file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return '不支持的图片格式，请上传 JPG/PNG/GIF/WebP'
    }
    if (file.size > MAX_SIZE) {
      return '图片大小不能超过 10MB'
    }
    const id = crypto.randomUUID?.() ?? Math.random().toString(36).slice(2)
    const previewUrl = URL.createObjectURL(file)
    setImages((prev) => [...prev, { id, file, previewUrl }])
    return null
  }, [])

  const removeImage = useCallback((id: string) => {
    setImages((prev) => {
      const img = prev.find((i) => i.id === id)
      if (img) URL.revokeObjectURL(img.previewUrl)
      return prev.filter((i) => i.id !== id)
    })
  }, [])

  const clearImages = useCallback(() => {
    setImages((prev) => {
      prev.forEach((i) => URL.revokeObjectURL(i.previewUrl))
      return []
    })
  }, [])

  const openFilePicker = useCallback(() => {
    inputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (!files) return
      for (let i = 0; i < files.length; i++) {
        const err = addImage(files[i]!)
        if (err) console.warn('[ImageUpload]', err)
      }
      // Reset so same file can be selected again
      e.target.value = ''
    },
    [addImage],
  )

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
            addImage(file)
          }
        }
      }
    },
    [addImage],
  )

  /** Upload images to vision API and return analysis text */
  const analyzeImages = useCallback(async (userQuestion?: string): Promise<string> => {
    if (images.length === 0) return ''
    setUploading(true)
    const results: string[] = []
    try {
      for (const img of images) {
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
            results.push(`🖼️ **图片分析${model}** — ${img.file.name}\n\n${data.description || data.analysis || ''}`)
          } else if (data.error) {
            results.push(`🖼️ **${img.file.name}** — ⚠️ 分析失败: ${data.error}`)
          }
        } catch {
          results.push(`🖼️ **${img.file.name}** — ⚠️ Vision 服务不可用`)
        }
      }
    } finally {
      setUploading(false)
    }
    return results.join('\n\n')
  }, [images])

  return {
    images,
    uploading,
    inputRef,
    addImage,
    removeImage,
    clearImages,
    openFilePicker,
    handleFileChange,
    handlePaste,
    analyzeImages,
    hasImages: images.length > 0,
  }
}
