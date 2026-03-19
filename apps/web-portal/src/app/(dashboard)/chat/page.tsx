'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { Loader2 } from 'lucide-react'
import { useStreamChat } from '@/hooks/useStreamChat'
import { useSessionManager } from '@/hooks/useSessionManager'
import { useSocketIO } from '@/hooks/useSocketIO'
import { useAuth } from '@/lib/auth/AuthProvider'
import { useVoice } from '@/hooks/useVoice'
import { useFileUpload } from '@/hooks/useFileUpload'
import { ChatHeader } from '@/components/chat/ChatHeader'
import { ChatEmptyState } from '@/components/chat/ChatEmptyState'
import { ChatMessageBubble } from '@/components/chat/ChatMessageBubble'
import { ChatInput } from '@/components/chat/ChatInput'
import { NotificationToast } from '@/components/proactive/NotificationToast'
import { AvatarPanel } from '@/components/avatar'

const SessionList = dynamic(() => import('@/components/chat/SessionList').then(m => ({ default: m.SessionList })), { ssr: false })
const SkillPanel = dynamic(() => import('@/components/chat/SkillPanel').then(m => ({ default: m.SkillPanel })), { ssr: false })

function uid() {
  return typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2) + Date.now().toString(36)
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking?: string
}

export default function ChatPage() {
  const { user } = useAuth()
  const realUserId = user?.id || 'anonymous'
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [skillPanelOpen, setSkillPanelOpen] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const pendingUserTextRef = useRef<string>('')

  const {
    sessions, currentSessionId, currentMessages, loading: sessionsLoading, messagesLoading,
    createSession, deleteSession, renameSession, selectSession, saveMessages,
  } = useSessionManager()

  const { notifications: proactiveMessages, dismissNotification: dismiss, dismissAll } = useSocketIO({ userId: realUserId, enabled: true })

  const { isRecording, isTranscribing, isSpeaking, startRecording, stopRecording, speak, stopSpeaking } = useVoice({
    onTranscript: (text) => setInput((prev) => prev + text),
    onError: (err) => console.warn('[Voice]', err),
  })

  const {
    files, images, documents, uploading: imageUploading, inputRef: fileInputRef,
    removeFile, clearFiles, openFilePicker, handleFileChange, handlePaste,
    analyzeImages, getDocumentTexts, hasFiles, hasImages, hasDocuments, isDocParsing, acceptTypes,
  } = useFileUpload()

  // 当选择会话后，加载历史消息到本地 state
  useEffect(() => {
    if (currentMessages.length > 0) {
      setMessages(currentMessages.map((m) => ({
        id: m.id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        thinking: m.thinking ? String(m.thinking) : undefined,
      })))
    } else if (currentSessionId) {
      setMessages([])
    }
  }, [currentMessages, currentSessionId])

  const { send, abort, isStreaming, content: streamContent, thinking: streamThinking, toolSteps, agentInfo, ragSources, brainInfo, brainPhase } = useStreamChat({
    onDone: (fullText) => {
      setMessages((prev) => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last && last.role === 'assistant') {
          last.content = fullText
          last.thinking = streamThinking || undefined
        }
        return updated
      })

      // 持久化用户消息 + AI 回复
      if (currentSessionId) {
        const userText = pendingUserTextRef.current
        void saveMessages(currentSessionId, [
          { role: 'user', content: userText },
          { role: 'assistant', content: fullText, thinking: streamThinking || undefined },
        ])
      }
    },
    onError: (err) => {
      setMessages((prev) => [
        ...prev,
        { id: uid(), role: 'assistant', content: `⚠ 错误: ${err.message}` },
      ])
    },
  })

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, streamContent, streamThinking, toolSteps])

  const handleNewChat = useCallback(async () => {
    const session = await createSession()
    if (session) {
      setMessages([])
      setInput('')
    }
  }, [createSession])

  const handleSelectSession = useCallback(async (id: string) => {
    await selectSession(id)
  }, [selectSession])

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text && !hasFiles) return
    if (isStreaming) return

    // 如果没有当前会话，自动创建一个
    let sid = currentSessionId
    if (!sid) {
      const session = await createSession()
      if (!session) return
      sid = session.id
    }

    // 拼接附件内容到消息中
    let finalText = text

    // 图片: 调用 Vision API 分析
    if (hasImages) {
      const analysis = await analyzeImages(text)
      if (analysis) {
        finalText = text ? `${text}\n\n${analysis}` : analysis
      }
    }

    // 文档: 注入解析后的文本
    if (hasDocuments) {
      const docTexts = getDocumentTexts()
      if (docTexts) {
        finalText = finalText ? `${finalText}\n\n${docTexts}` : docTexts
      }
    }

    // 显示内容: 只展示用户原始文字 + 附件指示（不暴露视觉/文档分析原文）
    let displayText = text
    if (hasImages) {
      const imgNames = files.filter(f => f.kind === 'image').map(f => f.file.name)
      displayText = displayText
        ? `${displayText}\n\n📎 已上传图片: ${imgNames.join(', ')}`
        : `📎 已上传图片: ${imgNames.join(', ')}`
    }
    if (hasDocuments) {
      const docNames = files.filter(f => f.kind === 'document').map(f => f.file.name)
      displayText = displayText
        ? `${displayText}\n\n📎 已上传文档: ${docNames.join(', ')}`
        : `📎 已上传文档: ${docNames.join(', ')}`
    }

    if (hasFiles) clearFiles()

    pendingUserTextRef.current = finalText

    const userMsg: Message = { id: uid(), role: 'user', content: displayText || text }
    const assistantMsg: Message = { id: uid(), role: 'assistant', content: '' }

    setMessages((prev) => [...prev, userMsg, assistantMsg])
    setInput('')

    await send(sid, finalText)
  }, [input, isStreaming, currentSessionId, createSession, send, files, hasFiles, hasImages, hasDocuments, analyzeImages, getDocumentTexts, clearFiles])

  const handleSelectSuggestion = useCallback((text: string) => {
    setInput(text)
  }, [])

  const sessionTitle = sessions.find((s) => s.id === currentSessionId)?.title || '对话'

  return (
    <div className="flex h-full">
      {/* 会话侧栏 */}
      {sidebarOpen && (
        <>
          <div className="md:hidden fixed inset-0 z-30 bg-black/50" onClick={() => setSidebarOpen(false)} aria-hidden="true" />
          <div className="max-md:fixed max-md:inset-y-0 max-md:left-0 max-md:z-40">
            <SessionList
              sessions={sessions}
              currentSessionId={currentSessionId}
              loading={sessionsLoading}
              onSelect={(id) => { handleSelectSession(id); if (window.innerWidth < 768) setSidebarOpen(false) }}
              onCreate={handleNewChat}
              onDelete={deleteSession}
              onRename={renameSession}
            />
          </div>
        </>
      )}

      {/* 主聊天区 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 主动通知 */}
        <NotificationToast messages={proactiveMessages} onDismiss={dismiss} onDismissAll={dismissAll} />

        {/* 头部 */}
        <ChatHeader
          title={sessionTitle}
          sidebarOpen={sidebarOpen}
          skillPanelOpen={skillPanelOpen}
          isStreaming={isStreaming}
          messagesLoading={messagesLoading}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onToggleSkillPanel={() => setSkillPanelOpen(!skillPanelOpen)}
        />

        {/* 消息区域 */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 sm:px-6 py-4 space-y-4 scrollbar-none">
          {messagesLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 size={24} className="animate-spin text-primary/40" />
            </div>
          ) : messages.length === 0 ? (
            <ChatEmptyState onSelectSuggestion={handleSelectSuggestion} />
          ) : (
            messages.map((msg, i) => (
              <ChatMessageBubble
                key={msg.id}
                msg={msg}
                isLast={i === messages.length - 1}
                isStreaming={isStreaming}
                streamContent={streamContent}
                streamThinking={streamThinking}
                toolSteps={toolSteps}
                agentInfo={agentInfo}
                ragSources={ragSources}
                brainInfo={brainInfo}
                brainPhase={brainPhase}
                isSpeaking={isSpeaking}
                onSpeak={speak}
                onStopSpeaking={stopSpeaking}
              />
            ))
          )}
        </div>

        {/* 虚拟形象 */}
        <AvatarPanel brainPhase={brainPhase} isStreaming={isStreaming} />

        {/* 输入区域 */}
        <ChatInput
          input={input}
          isStreaming={isStreaming}
          isRecording={isRecording}
          isTranscribing={isTranscribing}
          images={images}
          documents={documents}
          imageUploading={imageUploading}
          isDocParsing={isDocParsing}
          acceptTypes={acceptTypes}
          onInputChange={setInput}
          onSend={() => void handleSend()}
          onAbort={abort}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          onOpenFilePicker={openFilePicker}
          onRemoveImage={removeFile}
          onPaste={handlePaste}
          fileInputRef={fileInputRef}
          onFileChange={handleFileChange}
        />
      </div>

      {/* 技能面板 */}
      <SkillPanel
        open={skillPanelOpen}
        onClose={() => setSkillPanelOpen(false)}
        onInsertResult={(text) => setInput((prev) => prev + text)}
      />
    </div>
  )
}
