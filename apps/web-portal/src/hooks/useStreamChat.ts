'use client'

import { useState, useCallback, useRef } from 'react'

export interface ToolStep {
  type: 'tool_call' | 'observation'
  content: string
  tool_name?: string
  tool_input?: Record<string, unknown>
  tool_output?: string
}

export interface AgentInfo {
  agent: string
  description: string
}

export interface RagSource {
  title: string
  doc_id: string
  score: number
  snippet: string
}

export interface BrainInfo {
  taskType: string
  weights: { left: number; right: number }
  fusionStrategy: string
  confidence: number
  leftLatencyMs: number
  rightLatencyMs: number
  leftModel: string
  rightModel: string
  mode: 'dual' | 'triple' | 'quad' | 'brainstem'
  brainstemModel: string
  brainstemLatencyMs: number
  brainstemComplexity: string
  brainstemFocus: string
  brainstemReasoning: string
  taskComplexity: string
  qualityScore: number | null
  leftError: string | null
  rightError: string | null
  thalamusRoute: string | null
  thalamusLatencyMs: number
  thalamusReasoning: string
}

export type BrainPhase =
  | 'idle'
  | 'thalamus_routing'
  | 'thalamus_done'
  | 'brainstem_responding'
  | 'brainstem_analyzing'
  | 'cortex_activating'
  | 'thinking'
  | 'left_done'
  | 'right_done'
  | 'brainstem_directive'
  | 'fusing'
  | 'brainstem_reviewing'
  | 'done'

interface StreamChatOptions {
  apiUrl?: string
  onChunk?: (chunk: string) => void
  onThinking?: (text: string) => void
  onToolStep?: (step: ToolStep) => void
  onAgentInfo?: (info: AgentInfo) => void
  onRagSources?: (sources: RagSource[]) => void
  onBrainEvent?: (event: Record<string, unknown>) => void
  onDone?: (fullText: string) => void
  onError?: (error: Error) => void
}

export function useStreamChat(options: StreamChatOptions = {}) {
  const {
    apiUrl = '/api/chat/completions',
  } = options
  const [isStreaming, setIsStreaming] = useState(false)
  const [content, setContent] = useState('')
  const [thinking, setThinking] = useState('')
  const [toolSteps, setToolSteps] = useState<ToolStep[]>([])
  const [agentInfo, setAgentInfo] = useState<AgentInfo | null>(null)
  const [ragSources, setRagSources] = useState<RagSource[]>([])
  const [brainInfo, setBrainInfo] = useState<BrainInfo | null>(null)
  const [brainPhase, setBrainPhase] = useState<BrainPhase>('idle')
  const abortRef = useRef<AbortController | null>(null)

  const send = useCallback(async (sessionId: string, message: string) => {
    setIsStreaming(true)
    setContent('')
    setThinking('')
    setToolSteps([])
    setAgentInfo(null)
    setRagSources([])
    setBrainInfo(null)
    setBrainPhase('idle')
    let fullText = ''
    let fullThinking = ''

    abortRef.current = new AbortController()

    try {
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          content: message,
          stream: true,
          style: typeof window !== 'undefined' ? localStorage.getItem('dreamhelp_style') || 'default' : 'default',
          model: typeof window !== 'undefined' ? localStorage.getItem('dreamhelp_model') || undefined : undefined,
        }),
        signal: abortRef.current.signal,
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      if (!res.body) throw new Error('No response body')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let sseBuffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        sseBuffer += decoder.decode(value, { stream: true })
        const parts = sseBuffer.split('\n')
        // Keep the last (possibly incomplete) line in the buffer
        sseBuffer = parts.pop() || ''
        const lines = parts.filter((l) => l.startsWith('data: '))

        for (const line of lines) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') continue

          try {
            const parsed = JSON.parse(data)

            // RAG 引用来源
            if (parsed.type === 'rag_sources' && parsed.sources) {
              setRagSources(parsed.sources)
              options.onRagSources?.(parsed.sources)

            // 仿生大脑事件
            } else if (parsed.type === 'thalamus_routing') {
              setBrainPhase('thalamus_routing')
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'thalamus_result') {
              setBrainPhase('thalamus_done')
              const defaultBrain: BrainInfo = { taskType: '', weights: { left: 0.5, right: 0.5 }, fusionStrategy: '', confidence: 0, leftLatencyMs: 0, rightLatencyMs: 0, leftModel: '', rightModel: '', mode: 'dual', brainstemModel: '', brainstemLatencyMs: 0, brainstemComplexity: '', brainstemFocus: '', brainstemReasoning: '', taskComplexity: '', qualityScore: null, leftError: null, rightError: null, thalamusRoute: null, thalamusLatencyMs: 0, thalamusReasoning: '' }
              setBrainInfo((prev) => ({
                ...(prev || defaultBrain),
                thalamusRoute: parsed.route || null,
                thalamusLatencyMs: parsed.latency_ms || 0,
                thalamusReasoning: parsed.reasoning || '',
                taskType: parsed.task_type || '',
                weights: parsed.weights || { left: 0.5, right: 0.5 },
                taskComplexity: parsed.complexity || '',
              }))
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'brain_start') {
              setBrainPhase('thinking')
              setBrainInfo((prev) => prev ? {
                ...prev,
                taskType: parsed.task_type || prev.taskType,
                weights: parsed.weights || prev.weights,
                mode: parsed.mode || 'dual',
              } : prev)
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'brainstem_responding') {
              setBrainPhase('brainstem_responding')
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'cortex_activating') {
              setBrainPhase('cortex_activating')
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'brainstem_analyzing') {
              setBrainPhase('brainstem_analyzing')
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'left_thinking' || parsed.type === 'right_thinking') {
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'left_done') {
              setBrainPhase('left_done')
              setBrainInfo((prev) => prev ? { ...prev, leftLatencyMs: parsed.latency_ms || 0, leftError: parsed.error || null } : prev)
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'right_done') {
              setBrainPhase('right_done')
              setBrainInfo((prev) => prev ? { ...prev, rightLatencyMs: parsed.latency_ms || 0, rightError: parsed.error || null } : prev)
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'brainstem_directive') {
              setBrainPhase('brainstem_directive')
              setBrainInfo((prev) => prev ? {
                ...prev,
                brainstemComplexity: parsed.complexity || '',
                brainstemFocus: parsed.focus || '',
                brainstemReasoning: parsed.reasoning || '',
                brainstemLatencyMs: parsed.latency_ms || 0,
                fusionStrategy: parsed.strategy || prev.fusionStrategy,
                weights: parsed.weights || prev.weights,
              } : prev)
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'fusing') {
              setBrainPhase('fusing')
              setBrainInfo((prev) => prev ? { ...prev, fusionStrategy: parsed.strategy || '' } : prev)
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'brainstem_reviewing') {
              setBrainPhase('brainstem_reviewing')
              options.onBrainEvent?.(parsed)
            } else if (parsed.type === 'brain_done') {
              setBrainPhase('done')
              const md = parsed.metadata || {}
              setBrainInfo((prev) => prev ? {
                ...prev,
                confidence: md.confidence || 0,
                fusionStrategy: md.fusion_strategy || prev.fusionStrategy,
                leftLatencyMs: md.left_latency_ms || prev.leftLatencyMs,
                rightLatencyMs: md.right_latency_ms || prev.rightLatencyMs,
                leftModel: md.left_model || '',
                rightModel: md.right_model || '',
                brainstemModel: md.brainstem_model || '',
                brainstemLatencyMs: md.brainstem_latency_ms || prev.brainstemLatencyMs,
                taskComplexity: md.task_complexity || '',
                qualityScore: md.quality_score ?? null,
                thalamusRoute: md.thalamus_route || prev.thalamusRoute,
                thalamusLatencyMs: md.thalamus_latency_ms || prev.thalamusLatencyMs,
              } : prev)
              options.onBrainEvent?.(parsed)

            // Agent 路由信息
            } else if (parsed.type === 'agent_info') {
              const info: AgentInfo = { agent: parsed.agent, description: parsed.description }
              setAgentInfo(info)
              options.onAgentInfo?.(info)

            // 普通对话模式
            } else if (parsed.type === 'chunk' && parsed.content) {
              fullText += parsed.content
              setContent(fullText)
              options.onChunk?.(parsed.content)
            } else if (parsed.type === 'thinking' && parsed.content) {
              fullThinking += parsed.content
              setThinking(fullThinking)
              options.onThinking?.(parsed.content)

            // Agent 模式 — 工具调用步骤
            } else if (parsed.type === 'tool_call') {
              const step: ToolStep = {
                type: 'tool_call',
                content: parsed.content || '',
                tool_name: parsed.tool_name,
                tool_input: parsed.tool_input,
              }
              setToolSteps((prev) => [...prev, step])
              options.onToolStep?.(step)
            } else if (parsed.type === 'observation') {
              const step: ToolStep = {
                type: 'observation',
                content: parsed.content || '',
                tool_name: parsed.tool_name,
                tool_output: parsed.tool_output,
              }
              setToolSteps((prev) => [...prev, step])
              options.onToolStep?.(step)

            // Agent 最终回答
            } else if (parsed.type === 'final_answer') {
              const answer = parsed.final_answer || parsed.content || ''
              fullText = answer
              setContent(answer)

            } else if (parsed.type === 'error') {
              throw new Error(parsed.content || 'Unknown error')
            }
          } catch (e) {
            if (e instanceof SyntaxError) continue
            throw e
          }
        }
      }

      // Process any remaining data in the SSE buffer after stream ends
      if (sseBuffer.trim().startsWith('data: ')) {
        const remaining = sseBuffer.trim().slice(6).trim()
        if (remaining && remaining !== '[DONE]') {
          try {
            const parsed = JSON.parse(remaining)
            if (parsed.type === 'chunk' && parsed.content) {
              fullText += parsed.content
              setContent(fullText)
            }
          } catch { /* ignore incomplete final line */ }
        }
      }

      options.onDone?.(fullText)
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        options.onError?.(err)
      }
    } finally {
      setIsStreaming(false)
      setBrainPhase('idle')
      abortRef.current = null
    }
  }, [apiUrl, options])

  const abort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { send, abort, isStreaming, content, thinking, toolSteps, agentInfo, ragSources, brainInfo, brainPhase }
}
