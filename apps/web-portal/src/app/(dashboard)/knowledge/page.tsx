'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { BookOpen, Upload, Search, Trash2, FileText, Loader2, Eye, X, FileUp, CheckSquare, Square } from 'lucide-react'
import { cn } from '@/lib/utils'
import { FileDropZone } from '@/components/knowledge/FileDropZone'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogClose } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface DocItem {
  id: string
  title: string
  docType: string
  status: string
  chunkCount: number
  createdAt: string
  updatedAt: string
}

interface DocDetail {
  id: string
  title: string
  content: string | null
  docType: string
  status: string
  chunkCount: number
  createdAt: string
}

export default function KnowledgePage() {
  const t = useTranslations('knowledge')
  const tc = useTranslations('common')
  const [docs, setDocs] = useState<DocItem[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQ, setSearchQ] = useState('')
  const [uploading, setUploading] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadContent, setUploadContent] = useState('')
  const [uploadType, setUploadType] = useState('text')
  const [uploadMode, setUploadMode] = useState<'text' | 'file'>('text')
  const [viewDoc, setViewDoc] = useState<DocDetail | null>(null)
  const [viewLoading, setViewLoading] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [batchDeleting, setBatchDeleting] = useState(false)

  const loadDocs = useCallback(async (q?: string) => {
    setLoading(true)
    try {
      const url = q ? `/api/knowledge?q=${encodeURIComponent(q)}` : '/api/knowledge'
      const res = await fetch(url, { credentials: 'include' })
      const data = await res.json()
      if (data.success) {
        setDocs(data.documents || [])
      }
    } catch {
      console.error('[knowledge] load failed')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void loadDocs() }, [loadDocs])

  async function handleUpload() {
    if (!uploadContent.trim()) return
    setUploading(true)
    try {
      const res = await fetch('/api/knowledge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title: uploadTitle || undefined, content: uploadContent, type: uploadType }),
      })
      const data = await res.json()
      if (data.success) {
        setShowUpload(false)
        setUploadTitle('')
        setUploadContent('')
        void loadDocs()
      }
    } catch {
      console.error('[knowledge] upload failed')
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete(id: string) {
    try {
      const res = await fetch(`/api/knowledge/${id}`, { method: 'DELETE', credentials: 'include' })
      const data = await res.json()
      if (data.success) {
        setDocs((prev) => prev.filter((d) => d.id !== id))
      }
    } catch {
      console.error('[knowledge] delete failed')
    }
  }

  async function handleView(id: string) {
    setViewLoading(true)
    try {
      const res = await fetch(`/api/knowledge/${id}`, { credentials: 'include' })
      const data = await res.json()
      if (data.success) {
        setViewDoc(data.document)
      }
    } catch {
      console.error('[knowledge] view failed')
    } finally {
      setViewLoading(false)
    }
  }

  function handleSearch(q: string) {
    setSearchQ(q)
    void loadDocs(q || undefined)
  }

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    if (selected.size === docs.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(docs.map((d) => d.id)))
    }
  }

  async function handleBatchDelete() {
    if (selected.size === 0) return
    setBatchDeleting(true)
    try {
      await Promise.all(
        Array.from(selected).map((id) =>
          fetch(`/api/knowledge/${id}`, { method: 'DELETE', credentials: 'include' })
        )
      )
      setDocs((prev) => prev.filter((d) => !selected.has(d.id)))
      setSelected(new Set())
    } catch {
      console.error('[knowledge] batch delete failed')
    } finally {
      setBatchDeleting(false)
    }
  }

  const totalChunks = docs.reduce((sum, d) => sum + d.chunkCount, 0)

  function timeAgo(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime()
    const m = Math.floor(diff / 60000)
    if (m < 1) return t('justNow')
    if (m < 60) return t('minutesAgo', { m })
    const h = Math.floor(m / 60)
    if (h < 24) return t('hoursAgo', { h })
    return t('daysAgo', { d: Math.floor(h / 24) })
  }

  return (
    <div className="p-6 space-y-6">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-1 h-8 bg-primary rounded-full shadow-[0_0_8px_hsl(var(--primary)/0.4)]" />
          <div>
            <h1 className="font-display text-xl font-bold text-foreground tracking-wider">{t('title')}</h1>
            <p className="text-xs font-mono text-muted-foreground mt-0.5">{t('subtitle', { n: docs.length })}</p>
          </div>
        </div>
        <Button variant="cyber" size="sm" onClick={() => setShowUpload(true)} className="font-mono text-xs gap-1.5">
          <Upload size={13} />
          {t('upload')}
        </Button>
      </div>

      {/* 统计卡片 */}
      {!loading && docs.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <Card className="text-center">
            <CardContent className="p-3">
              <div className="text-lg font-display font-bold text-primary">{docs.length}</div>
              <div className="text-[10px] font-mono text-muted-foreground">{t('docCount')}</div>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="p-3">
              <div className="text-lg font-display font-bold text-cyan-400">{totalChunks}</div>
              <div className="text-[10px] font-mono text-muted-foreground">{t('chunkCount')}</div>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="p-3">
              <div className="text-lg font-display font-bold text-emerald-400">{docs.filter((d) => d.status === 'ready').length}</div>
              <div className="text-[10px] font-mono text-muted-foreground">{t('readyCount')}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 搜索 + 批量操作 */}
      <div className="flex items-center gap-2">
        <div className="flex-1 flex items-center gap-2">
          <Search size={14} className="text-muted-foreground shrink-0" />
          <Input
            type="text"
            value={searchQ}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder={t('searchPlaceholder')}
            className="font-mono text-xs"
          />
        </div>
        {selected.size > 0 && (
          <Button variant="cyber" size="sm" onClick={handleBatchDelete} disabled={batchDeleting} className="font-mono text-xs gap-1.5 whitespace-nowrap">
            <Trash2 size={12} />
            {t('batchDelete', { n: selected.size })}
          </Button>
        )}
      </div>

      {/* 文档列表 */}
      {loading ? (
        <div className="flex justify-center py-16"><Loader2 size={20} className="animate-spin text-muted-foreground" /></div>
      ) : docs.length === 0 ? (
        <div className="text-center py-16 space-y-3">
          <BookOpen size={32} className="mx-auto text-muted-foreground/20" />
          <p className="text-sm font-mono text-muted-foreground/50">{t('noDocs')}</p>
          <Button variant="link" size="sm" onClick={() => setShowUpload(true)} className="font-mono text-xs">
            {t('uploadFirst')}
          </Button>
        </div>
      ) : (
        <div className="space-y-2">
          {/* 全选 */}
          <div className="flex items-center gap-2 px-3 py-1">
            <button onClick={toggleSelectAll} className="text-muted-foreground/40 hover:text-muted-foreground transition-colors">
              {selected.size === docs.length ? <CheckSquare size={14} /> : <Square size={14} />}
            </button>
            <span className="text-[10px] font-mono text-muted-foreground/40">
              {selected.size > 0 ? t('selected', { s: selected.size, t: docs.length }) : t('selectAll')}
            </span>
          </div>
          {docs.map((doc) => (
            <Card key={doc.id} className={cn(
              'hover:border-primary/30 transition-colors group',
              selected.has(doc.id) && 'border-primary/30 bg-primary/5',
            )}>
              <CardContent className="flex items-center gap-3 p-3">
                <button onClick={() => toggleSelect(doc.id)} className="text-muted-foreground/40 hover:text-muted-foreground transition-colors flex-shrink-0">
                  {selected.has(doc.id) ? <CheckSquare size={14} className="text-primary" /> : <Square size={14} />}
                </button>
                <FileText size={16} className="text-muted-foreground/40 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-mono font-bold text-foreground truncate">{doc.title}</div>
                  <div className="text-[10px] font-mono text-muted-foreground/50 mt-0.5">
                    {doc.docType} · {t('chunks', { n: doc.chunkCount })} · {timeAgo(doc.createdAt)}
                  </div>
                </div>
                <Badge variant={doc.status === 'ready' ? 'success' : 'secondary'} className="text-[9px] px-1.5 py-0 h-5">
                  {doc.status === 'ready' ? t('ready') : doc.status}
                </Badge>
                <Button variant="ghost" size="icon-xs" onClick={() => handleView(doc.id)} className="text-muted-foreground/30 hover:text-cyan-400">
                  <Eye size={14} />
                </Button>
                <Button variant="ghost" size="icon-xs" onClick={() => handleDelete(doc.id)} className="text-muted-foreground/30 hover:text-primary">
                  <Trash2 size={14} />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 上传弹窗 */}
      <Dialog open={showUpload} onOpenChange={setShowUpload}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-sm font-mono">{t('upload')}</DialogTitle>
          </DialogHeader>

          <Tabs value={uploadMode} onValueChange={(v) => setUploadMode(v as 'text' | 'file')}>
            <TabsList className="w-full">
              <TabsTrigger value="text" className="flex-1 text-[10px] font-mono gap-1.5">
                <Upload size={11} /> {t('uploadText')}
              </TabsTrigger>
              <TabsTrigger value="file" className="flex-1 text-[10px] font-mono gap-1.5">
                <FileUp size={11} /> {t('uploadFile')}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="text" className="space-y-3 mt-3">
              <div className="space-y-1.5">
                <Label className="text-[10px] font-mono text-muted-foreground">{t('titleOptional')}</Label>
                <Input
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder={t('titlePlaceholder')}
                  className="font-mono text-xs"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] font-mono text-muted-foreground">{t('type')}</Label>
                <div className="flex gap-2">
                  {['text', 'markdown', 'faq'].map((typ) => (
                    <button
                      key={typ}
                      onClick={() => setUploadType(typ)}
                      className={cn(
                        'px-2 py-1 text-[10px] font-mono border transition-colors rounded-md',
                        uploadType === typ ? 'bg-primary/10 border-primary/30 text-primary' : 'border-border text-muted-foreground hover:text-foreground',
                      )}
                    >
                      {typ}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] font-mono text-muted-foreground">{t('content')}</Label>
                <Textarea
                  value={uploadContent}
                  onChange={(e) => setUploadContent(e.target.value)}
                  rows={10}
                  placeholder={t('contentPlaceholder')}
                  className="font-mono text-xs resize-none"
                />
                <div className="text-[9px] font-mono text-muted-foreground/40 text-right">
                  {t('chars', { n: uploadContent.length })}
                </div>
              </div>
              <Button
                variant="cyber"
                size="sm"
                onClick={handleUpload}
                disabled={uploading || !uploadContent.trim()}
                className="w-full font-mono text-xs gap-1.5"
              >
                {uploading ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} />}
                {uploading ? t('uploading') : t('upload')}
              </Button>
            </TabsContent>

            <TabsContent value="file" className="mt-3">
              <FileDropZone onUploadComplete={() => { setShowUpload(false); void loadDocs() }} />
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      {/* 文档详情弹窗 */}
      <Dialog open={!!(viewDoc || viewLoading)} onOpenChange={() => setViewDoc(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="text-sm font-mono truncate">
              {viewDoc?.title || tc('loading')}
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto">
            {viewLoading ? (
              <div className="flex justify-center py-8"><Loader2 size={16} className="animate-spin text-muted-foreground" /></div>
            ) : viewDoc ? (
              <div className="space-y-3">
                <div className="flex gap-3 text-[10px] font-mono text-muted-foreground/50">
                  <span>{t('docType')}: {viewDoc.docType}</span>
                  <span>{t('chunkCountLabel')}: {viewDoc.chunkCount}</span>
                  <span>{t('status')}: {viewDoc.status}</span>
                </div>
                <pre className="text-xs font-mono text-foreground whitespace-pre-wrap break-words bg-secondary border border-border rounded-md p-4 max-h-96 overflow-y-auto scrollbar-none">
                  {viewDoc.content || t('noContent')}
                </pre>
              </div>
            ) : null}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
