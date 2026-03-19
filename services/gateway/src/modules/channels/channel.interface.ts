/**
 * 多渠道抽象层 — 统一消息格式（Phase 6）
 */

/** 渠道类型 */
export type ChannelType = 'web' | 'wechat' | 'wecom' | 'telegram'

/** 统一入站消息格式 */
export interface InboundMessage {
  channelType: ChannelType
  channelUserId: string       // 渠道内用户 ID
  channelMessageId?: string   // 渠道内消息 ID
  content: string             // 文本内容
  messageType: 'text' | 'image' | 'voice' | 'video' | 'file' | 'event'
  sessionId?: string          // 会话 ID（可选，渠道自动生成）
  raw?: unknown               // 原始消息体
}

/** 统一出站消息格式 */
export interface OutboundMessage {
  channelType: ChannelType
  channelUserId: string
  content: string
  messageType: 'text' | 'markdown' | 'image' | 'voice'
  replyToMessageId?: string
}

/** 渠道适配器接口 */
export interface ChannelAdapter {
  readonly channelType: ChannelType

  /** 验证 webhook 签名 */
  verifySignature(headers: Record<string, string>, body: unknown): boolean

  /** 解析入站消息 */
  parseInbound(body: unknown): InboundMessage | null

  /** 格式化出站消息 */
  formatOutbound(msg: OutboundMessage): unknown

  /** 发送消息到渠道 */
  sendMessage(msg: OutboundMessage): Promise<void>
}
