export interface Agent {
  id: string
  name: string
  description?: string
  avatarUrl?: string
  type: 'preset' | 'custom' | 'workflow'
  modelProvider: string
  modelName: string
  temperature: number
  maxTokens: number
  capabilities: string[]
  tools: string[]
  status: 'active' | 'inactive' | 'draft'
  isPublic: boolean
  usageCount: number
  createdAt: string
  updatedAt: string
}

export interface CreateAgentRequest {
  name: string
  description?: string
  type?: 'custom' | 'workflow'
  systemPrompt: string
  modelProvider?: string
  modelName?: string
  temperature?: number
  maxTokens?: number
  tools?: string[]
}

export interface UpdateAgentRequest extends Partial<CreateAgentRequest> {
  status?: 'active' | 'inactive' | 'draft'
}
