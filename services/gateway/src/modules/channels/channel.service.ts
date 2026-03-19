/**
 * 多渠道消息处理服务（Phase 6）
 *
 * 统一处理流程: 渠道消息 → 解析 → 用户映射 → brain-core → 格式化 → 回复
 */

import { Injectable } from '@nestjs/common'
import type { ChannelAdapter, ChannelType, InboundMessage, OutboundMessage } from './channel.interface'
import { WechatAdapter } from './adapters/wechat.adapter'
import { WecomAdapter } from './adapters/wecom.adapter'
import { TelegramAdapter } from './adapters/telegram.adapter'
import { UserMappingService } from './user-mapping.service'

const BRAIN_CORE_URL = process.env.BRAIN_CORE_URL || 'http://127.0.0.1:8000'

/** 消息处理统计 */
export interface ChannelMetrics {
  received: number
  replied: number
  errors: number
  lastMessageAt?: Date
}

@Injectable()
export class ChannelService {
  private adapters: Map<ChannelType, ChannelAdapter> = new Map()
  private metrics: Map<ChannelType, ChannelMetrics> = new Map()

  constructor(private readonly userMapping: UserMappingService) {
    this.adapters.set('wechat', new WechatAdapter())
    this.adapters.set('wecom', new WecomAdapter())
    this.adapters.set('telegram', new TelegramAdapter())

    // 初始化指标
    for (const t of ['wechat', 'wecom', 'telegram'] as ChannelType[]) {
      this.metrics.set(t, { received: 0, replied: 0, errors: 0 })
    }
  }

  getAdapter(type: ChannelType): ChannelAdapter | undefined {
    return this.adapters.get(type)
  }

  /** 处理入站消息：解析 → 用户映射 → brain-core → 回复 */
  async handleInbound(channelType: ChannelType, body: unknown): Promise<string | null> {
    const adapter = this.adapters.get(channelType)
    if (!adapter) {
      console.error(`[Channel] Unknown channel type: ${channelType}`)
      return null
    }

    const m = this.metrics.get(channelType)!
    m.received++
    m.lastMessageAt = new Date()

    const inbound = adapter.parseInbound(body)
    if (!inbound) return null

    // 记录用户映射
    await this.userMapping.getOrCreateMapping(
      channelType,
      inbound.channelUserId,
      (inbound.raw as Record<string, unknown>)?.from_name as string | undefined,
    )

    // 事件消息特殊处理
    if (inbound.messageType === 'event') {
      return this.handleEvent(adapter, inbound)
    }

    // 调用 brain-core 获取回复
    try {
      const reply = await this.callBrainCore(inbound)

      // 构建出站消息
      const outbound: OutboundMessage = {
        channelType,
        channelUserId: inbound.channelUserId,
        content: reply,
        messageType: 'text',
        replyToMessageId: inbound.channelMessageId,
      }

      // Telegram 等需要主动发送（非被动回复）
      if (channelType === 'telegram') {
        await adapter.sendMessage(outbound)
        m.replied++
        return null
      }

      // 微信/企微返回被动回复 XML
      m.replied++
      return adapter.formatOutbound(outbound) as string
    } catch (e) {
      m.errors++
      console.error(`[Channel:${channelType}] Error:`, e)
      const errorOutbound: OutboundMessage = {
        channelType,
        channelUserId: inbound.channelUserId,
        content: '抱歉，处理您的消息时出现问题，请稍后再试。',
        messageType: 'text',
      }
      if (channelType === 'telegram') {
        await adapter.sendMessage(errorOutbound).catch(() => {})
        return null
      }
      return adapter.formatOutbound(errorOutbound) as string
    }
  }

  /** 处理事件消息 */
  private async handleEvent(adapter: ChannelAdapter, msg: InboundMessage): Promise<string | null> {
    if (msg.content === '__subscribe__') {
      const welcome: OutboundMessage = {
        channelType: msg.channelType,
        channelUserId: msg.channelUserId,
        content: '你好！我是梦帮小助 🤖\n\nDREAMVFIA 出品的 AI 智能助手，我可以帮你：\n• 回答各类问题\n• 编写代码\n• 翻译文案\n• 数学计算\n• 信息搜索\n\n直接发消息给我就可以开始对话啦！',
        messageType: 'text',
      }
      return adapter.formatOutbound(welcome) as string
    }
    return null
  }

  /** 调用 brain-core 获取 AI 回复 */
  private async callBrainCore(msg: InboundMessage): Promise<string> {
    const sessionId = this.userMapping.getSessionId(msg.channelType, msg.channelUserId)

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 55_000) // 微信 5s 限制，留 buffer

    try {
      const resp = await fetch(`${BRAIN_CORE_URL}/api/v1/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          content: msg.content,
          stream: false,
        }),
        signal: controller.signal,
      })

      if (!resp.ok) {
        console.error(`[Channel] brain-core error: ${resp.status}`)
        return '抱歉，我暂时无法处理您的请求，请稍后再试。'
      }

      const data = await resp.json() as { content: string }
      return data.content || '抱歉，我没有理解您的问题。'
    } catch (e: unknown) {
      if ((e as Error).name === 'AbortError') {
        return '抱歉，处理时间较长，请稍后再发送一次。'
      }
      console.error(`[Channel] brain-core call failed:`, e)
      return '抱歉，服务暂时不可用，请稍后再试。'
    } finally {
      clearTimeout(timeout)
    }
  }

  /** 绑定渠道用户到已有系统账号 */
  async bindChannelUser(channel: string, channelUserId: string, targetUserId: string): Promise<boolean> {
    return this.userMapping.bindToUser(channel, channelUserId, targetUserId)
  }

  /** 列出渠道用户映射 */
  async listChannelUsers(channel?: string, limit = 50) {
    return this.userMapping.listMappings(channel, limit)
  }

  /** 获取所有渠道状态 */
  async getChannelStats(): Promise<Record<string, { configured: boolean; metrics: ChannelMetrics; userMapping?: any }>> {
    const mappingStats = await this.userMapping.getStats()
    return {
      wechat: {
        configured: !!process.env.WECHAT_APP_ID,
        metrics: this.metrics.get('wechat')!,
        userMapping: { count: mappingStats.byChannel['wechat'] || 0 },
      },
      wecom: {
        configured: !!process.env.WECOM_CORP_ID,
        metrics: this.metrics.get('wecom')!,
        userMapping: { count: mappingStats.byChannel['wecom'] || 0 },
      },
      telegram: {
        configured: !!process.env.TELEGRAM_BOT_TOKEN,
        metrics: this.metrics.get('telegram')!,
        userMapping: { count: mappingStats.byChannel['telegram'] || 0 },
      },
    }
  }
}
