/**
 * 微信公众号渠道适配器（Phase 6）
 *
 * 接入文档: https://developers.weixin.qq.com/doc/offiaccount/Message_Management/
 * 需要配置: WECHAT_APP_ID, WECHAT_APP_SECRET, WECHAT_TOKEN
 *
 * 支持: 文本消息、图片消息、语音消息、关注事件、客服消息主动推送
 */

import * as crypto from 'crypto'
import type { ChannelAdapter, InboundMessage, OutboundMessage } from '../channel.interface'

const WECHAT_TOKEN = process.env.WECHAT_TOKEN || 'dreamhelp_wechat_token'
const WECHAT_APP_ID = process.env.WECHAT_APP_ID || ''
const WECHAT_APP_SECRET = process.env.WECHAT_APP_SECRET || ''

interface WechatXmlMessage {
  ToUserName: string
  FromUserName: string
  CreateTime: string
  MsgType: string
  Content?: string
  MsgId?: string
  Event?: string
  EventKey?: string
  PicUrl?: string
  MediaId?: string
  Format?: string
  Recognition?: string
}

/** access_token 缓存 */
let cachedToken: { token: string; expiresAt: number } | null = null

export class WechatAdapter implements ChannelAdapter {
  readonly channelType = 'wechat' as const

  verifySignature(headers: Record<string, string>, body: unknown): boolean {
    const query = body as Record<string, string>
    const { signature, timestamp, nonce } = query
    if (!signature || !timestamp || !nonce) return false

    const arr = [WECHAT_TOKEN, timestamp, nonce].sort()
    const hash = crypto.createHash('sha1').update(arr.join('')).digest('hex')
    return hash === signature
  }

  parseInbound(body: unknown): InboundMessage | null {
    const xml = body as WechatXmlMessage
    if (!xml || !xml.FromUserName || !xml.MsgType) return null

    // 事件消息（关注/取关等）
    if (xml.MsgType === 'event') {
      if (xml.Event === 'subscribe') {
        return {
          channelType: 'wechat',
          channelUserId: xml.FromUserName,
          content: '__subscribe__',
          messageType: 'event',
          raw: xml,
        }
      }
      return null
    }

    // 文本消息
    if (xml.MsgType === 'text' && xml.Content) {
      return {
        channelType: 'wechat',
        channelUserId: xml.FromUserName,
        channelMessageId: xml.MsgId,
        content: xml.Content,
        messageType: 'text',
        sessionId: `wechat_${xml.FromUserName}`,
        raw: xml,
      }
    }

    // 图片消息
    if (xml.MsgType === 'image' && xml.PicUrl) {
      return {
        channelType: 'wechat',
        channelUserId: xml.FromUserName,
        channelMessageId: xml.MsgId,
        content: `[图片] ${xml.PicUrl}`,
        messageType: 'image',
        sessionId: `wechat_${xml.FromUserName}`,
        raw: xml,
      }
    }

    // 语音消息（含识别结果）
    if (xml.MsgType === 'voice') {
      const content = xml.Recognition
        ? xml.Recognition  // 微信自带语音识别
        : '[语音消息] 请发送文字消息'
      return {
        channelType: 'wechat',
        channelUserId: xml.FromUserName,
        channelMessageId: xml.MsgId,
        content,
        messageType: xml.Recognition ? 'text' : 'voice',
        sessionId: `wechat_${xml.FromUserName}`,
        raw: xml,
      }
    }

    return null
  }

  formatOutbound(msg: OutboundMessage): string {
    const timestamp = Math.floor(Date.now() / 1000)
    const content = msg.content.length > 2000
      ? msg.content.slice(0, 1997) + '...'
      : msg.content
    return `<xml>
  <ToUserName><![CDATA[${msg.channelUserId}]]></ToUserName>
  <FromUserName><![CDATA[${WECHAT_APP_ID}]]></FromUserName>
  <CreateTime>${timestamp}</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[${this.stripMarkdown(content)}]]></Content>
</xml>`
  }

  /** 获取 access_token (带缓存，有效期 2 小时) */
  async getAccessToken(): Promise<string | null> {
    if (!WECHAT_APP_ID || !WECHAT_APP_SECRET) return null

    // 检查缓存
    if (cachedToken && Date.now() < cachedToken.expiresAt) {
      return cachedToken.token
    }

    try {
      const resp = await fetch(
        `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${WECHAT_APP_ID}&secret=${WECHAT_APP_SECRET}`
      )
      const data = await resp.json() as { access_token?: string; expires_in?: number; errcode?: number }

      if (data.access_token && data.expires_in) {
        cachedToken = {
          token: data.access_token,
          expiresAt: Date.now() + (data.expires_in - 300) * 1000, // 提前 5 分钟刷新
        }
        return data.access_token
      }

      console.error(`[Wechat] Get access_token failed: errcode=${data.errcode}`)
      return null
    } catch (e) {
      console.error(`[Wechat] Get access_token error:`, e)
      return null
    }
  }

  /** 主动发送客服消息 */
  async sendMessage(msg: OutboundMessage): Promise<void> {
    const token = await this.getAccessToken()
    if (!token) {
      console.log(`[Wechat] No access_token, skip send to ${msg.channelUserId}`)
      return
    }

    const content = this.stripMarkdown(
      msg.content.length > 2000 ? msg.content.slice(0, 1997) + '...' : msg.content
    )

    try {
      const resp = await fetch(
        `https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=${token}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            touser: msg.channelUserId,
            msgtype: 'text',
            text: { content },
          }),
        }
      )
      const data = await resp.json() as { errcode?: number; errmsg?: string }
      if (data.errcode && data.errcode !== 0) {
        console.error(`[Wechat] Send message error: ${data.errcode} ${data.errmsg}`)
      }
    } catch (e) {
      console.error(`[Wechat] Send failed:`, e)
    }
  }

  /** 去除 Markdown 格式（微信不支持） */
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
