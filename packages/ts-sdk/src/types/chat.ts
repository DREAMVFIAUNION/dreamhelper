export interface ChatMessage {
  id: string
  sessionId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  thinking?: ThinkingStep[]
  toolCalls?: ToolCall[]
  tokens?: number
  latencyMs?: number
  createdAt: string
}

export interface ThinkingStep {
  type: 'thinking' | 'observation'
  tool?: string
  text: string
}

export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, unknown>
  result?: string
}

export interface ChatSession {
  id: string
  userId: string
  agentId: string
  title?: string
  status: 'active' | 'archived'
  messageCount: number
  createdAt: string
  updatedAt: string
}

export interface SendMessageRequest {
  sessionId: string
  content: string
  stream?: boolean
}

export interface CreateSessionRequest {
  agentId: string
  title?: string
}
