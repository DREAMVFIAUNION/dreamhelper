/** 所有 WebSocket / SSE 事件的联合类型 */
export type AppEvent =
  | ChatStreamEvent
  | NotificationEvent
  | AgentStatusEvent
  | SystemEvent

export interface ChatStreamEvent {
  type: 'chat.stream'
  sessionId: string
  data: {
    chunk?: string
    thinking?: { type: 'thinking' | 'observation'; tool?: string; text: string }
    done?: boolean
    usage?: { promptTokens: number; completionTokens: number }
  }
}

export interface NotificationEvent {
  type: 'notification'
  data: {
    id: string
    level: 'info' | 'warning' | 'error'
    title: string
    message: string
    timestamp: string
  }
}

export interface AgentStatusEvent {
  type: 'agent.status'
  data: {
    agentId: string
    status: 'idle' | 'thinking' | 'executing' | 'error'
    currentTool?: string
  }
}

export interface SystemEvent {
  type: 'system'
  data: {
    action: 'connected' | 'disconnected' | 'heartbeat' | 'error'
    message?: string
  }
}
