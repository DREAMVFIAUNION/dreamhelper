/**
 * Telegram Bot 渠道适配器（Phase 6）
 *
 * 接入文档: https://core.telegram.org/bots/api
 * 需要配置: TELEGRAM_BOT_TOKEN
 *
 * 支持消息类型: text, photo, voice, document, sticker, /start 命令
 */

import type { ChannelAdapter, InboundMessage, OutboundMessage } from '../channel.interface'

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || ''
const TELEGRAM_API = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}`

interface TelegramUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
}

interface TelegramMessage {
  message_id: number
  from: TelegramUser
  chat: { id: number; type: string }
  date: number
  text?: string
  photo?: Array<{ file_id: string; width: number; height: number }>
  voice?: { file_id: string; duration: number }
  document?: { file_id: string; file_name?: string; mime_type?: string }
  sticker?: { file_id: string; emoji?: string }
  caption?: string
  entities?: Array<{ type: string; offset: number; length: number }>
}

interface TelegramUpdate {
  update_id: number
  message?: TelegramMessage
}

export class TelegramAdapter implements ChannelAdapter {
  readonly channelType = 'telegram' as const

  verifySignature(headers: Record<string, string>, body: unknown): boolean {
    const secret = process.env.TELEGRAM_WEBHOOK_SECRET || ''
    if (!secret) return true
    return headers['x-telegram-bot-api-secret-token'] === secret
  }

  parseInbound(body: unknown): InboundMessage | null {
    const update = body as TelegramUpdate
    const msg = update?.message
    if (!msg) return null

    const chatId = String(msg.chat.id)
    const displayName = [msg.from.first_name, msg.from.last_name].filter(Boolean).join(' ')

    // /start 命令 → 关注事件
    if (msg.text?.startsWith('/start')) {
      return {
        channelType: 'telegram',
        channelUserId: chatId,
        content: '__subscribe__',
        messageType: 'event',
        sessionId: `telegram_${chatId}`,
        raw: { ...update, from_name: displayName },
      }
    }

    // 文本消息
    if (msg.text) {
      return {
        channelType: 'telegram',
        channelUserId: chatId,
        channelMessageId: String(msg.message_id),
        content: msg.text,
        messageType: 'text',
        sessionId: `telegram_${chatId}`,
        raw: { ...update, from_name: displayName },
      }
    }

    // 图片消息 → 转为文字描述请求
    if (msg.photo && msg.photo.length > 0) {
      const caption = msg.caption || '请描述这张图片'
      return {
        channelType: 'telegram',
        channelUserId: chatId,
        channelMessageId: String(msg.message_id),
        content: `[图片] ${caption}`,
        messageType: 'image',
        sessionId: `telegram_${chatId}`,
        raw: { ...update, from_name: displayName, photo_file_id: msg.photo.at(-1)?.file_id },
      }
    }

    // 语音消息 → 提示用户
    if (msg.voice) {
      return {
        channelType: 'telegram',
        channelUserId: chatId,
        channelMessageId: String(msg.message_id),
        content: '[语音消息] 目前暂不支持语音识别，请发送文字消息。',
        messageType: 'voice',
        sessionId: `telegram_${chatId}`,
        raw: { ...update, from_name: displayName },
      }
    }

    // 贴纸 → 转为 emoji
    if (msg.sticker?.emoji) {
      return {
        channelType: 'telegram',
        channelUserId: chatId,
        channelMessageId: String(msg.message_id),
        content: msg.sticker.emoji,
        messageType: 'text',
        sessionId: `telegram_${chatId}`,
        raw: { ...update, from_name: displayName },
      }
    }

    return null
  }

  formatOutbound(msg: OutboundMessage): unknown {
    // 长消息分段 (Telegram 限制 4096 字符)
    const text = msg.content.length > 4000
      ? msg.content.slice(0, 3997) + '...'
      : msg.content

    return {
      chat_id: msg.channelUserId,
      text,
      parse_mode: 'Markdown',
      reply_to_message_id: msg.replyToMessageId
        ? parseInt(msg.replyToMessageId)
        : undefined,
    }
  }

  async sendMessage(msg: OutboundMessage): Promise<void> {
    if (!TELEGRAM_BOT_TOKEN) {
      console.log(`[Telegram] Not configured, skip send to ${msg.channelUserId}`)
      return
    }

    const payload = this.formatOutbound(msg)

    try {
      const resp = await fetch(`${TELEGRAM_API}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!resp.ok) {
        // Markdown 解析失败时回退到纯文本
        const fallback = {
          ...(payload as Record<string, unknown>),
          parse_mode: undefined,
          text: this.stripMarkdown(msg.content),
        }
        await fetch(`${TELEGRAM_API}/sendMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(fallback),
        })
      }
    } catch (e) {
      console.error(`[Telegram] Send failed:`, e)
    }
  }

  /** 设置 Webhook URL (调用一次即可) */
  async setWebhook(url: string): Promise<boolean> {
    if (!TELEGRAM_BOT_TOKEN) return false
    try {
      const payload: Record<string, unknown> = { url }
      const secret = process.env.TELEGRAM_WEBHOOK_SECRET
      if (secret) payload.secret_token = secret
      const resp = await fetch(`${TELEGRAM_API}/setWebhook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await resp.json() as { ok: boolean; description?: string }
      console.log(`[Telegram] setWebhook: ${data.ok} — ${data.description || ''}`)
      return data.ok
    } catch (e) {
      console.error(`[Telegram] setWebhook failed:`, e)
      return false
    }
  }

  /** Telegram Markdown 不支持的格式降级 */
  private stripMarkdown(text: string): string {
    return text
      .replace(/```[\s\S]*?```/g, (m) => m.replace(/```\w*\n?/g, '').trim())
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/#{1,6}\s/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
  }
}
