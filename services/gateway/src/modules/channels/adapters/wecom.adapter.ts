/**
 * 企业微信渠道适配器（Phase 6）
 *
 * 接入文档: https://developer.work.weixin.qq.com/document/path/90930
 * 需要配置: WECOM_CORP_ID, WECOM_AGENT_ID, WECOM_SECRET, WECOM_TOKEN, WECOM_ENCODING_AES_KEY
 */

import * as crypto from 'crypto'
import type { ChannelAdapter, InboundMessage, OutboundMessage } from '../channel.interface'

const WECOM_TOKEN = process.env.WECOM_TOKEN || 'dreamhelp_wecom_token'
const WECOM_CORP_ID = process.env.WECOM_CORP_ID || ''
const WECOM_SECRET = process.env.WECOM_SECRET || ''
const WECOM_AGENT_ID = process.env.WECOM_AGENT_ID || ''

interface WecomMessage {
  ToUserName: string
  FromUserName: string
  CreateTime: string
  MsgType: string
  Content?: string
  MsgId?: string
  AgentID?: string
  Event?: string
}

export class WecomAdapter implements ChannelAdapter {
  readonly channelType = 'wecom' as const

  verifySignature(headers: Record<string, string>, body: unknown): boolean {
    const query = body as Record<string, string>
    const { msg_signature, timestamp, nonce } = query
    if (!msg_signature || !timestamp || !nonce) return false

    const arr = [WECOM_TOKEN, timestamp, nonce].sort()
    const hash = crypto.createHash('sha1').update(arr.join('')).digest('hex')
    return hash === msg_signature
  }

  parseInbound(body: unknown): InboundMessage | null {
    const msg = body as WecomMessage
    if (!msg || !msg.FromUserName || !msg.MsgType) return null

    if (msg.MsgType === 'text' && msg.Content) {
      return {
        channelType: 'wecom',
        channelUserId: msg.FromUserName,
        channelMessageId: msg.MsgId,
        content: msg.Content,
        messageType: 'text',
        sessionId: `wecom_${msg.FromUserName}`,
        raw: msg,
      }
    }

    if (msg.MsgType === 'event') {
      return {
        channelType: 'wecom',
        channelUserId: msg.FromUserName,
        content: `__${msg.Event}__`,
        messageType: 'event',
        raw: msg,
      }
    }

    return null
  }

  formatOutbound(msg: OutboundMessage): unknown {
    // 企业微信被动回复 XML
    const timestamp = Math.floor(Date.now() / 1000)
    const content = msg.content.length > 2000
      ? msg.content.slice(0, 1997) + '...'
      : msg.content
    return `<xml>
  <ToUserName><![CDATA[${msg.channelUserId}]]></ToUserName>
  <FromUserName><![CDATA[${WECOM_CORP_ID}]]></FromUserName>
  <CreateTime>${timestamp}</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[${content}]]></Content>
</xml>`
  }

  async sendMessage(msg: OutboundMessage): Promise<void> {
    // 企业微信主动推送（需要 access_token）
    if (!WECOM_CORP_ID || !WECOM_SECRET) {
      console.log(`[Wecom] Not configured, skip send to ${msg.channelUserId}`)
      return
    }

    try {
      // 获取 access_token
      const tokenResp = await fetch(
        `https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=${WECOM_CORP_ID}&corpsecret=${WECOM_SECRET}`
      )
      const tokenData = await tokenResp.json() as { access_token: string }

      // 发送消息
      await fetch(
        `https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=${tokenData.access_token}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            touser: msg.channelUserId,
            msgtype: 'text',
            agentid: parseInt(WECOM_AGENT_ID),
            text: { content: msg.content.slice(0, 2048) },
          }),
        }
      )
    } catch (e) {
      console.error(`[Wecom] Send failed:`, e)
    }
  }
}
