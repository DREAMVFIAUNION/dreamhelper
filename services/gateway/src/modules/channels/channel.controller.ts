/**
 * 多渠道 Webhook 控制器（Phase 6）
 *
 * 路由:
 *   POST /webhook/wechat    — 微信公众号
 *   POST /webhook/wecom     — 企业微信
 *   POST /webhook/telegram  — Telegram Bot
 *   GET  /webhook/wechat    — 微信服务器验证
 *   GET  /webhook/wecom     — 企微服务器验证
 *   GET  /channels/stats    — 渠道状态
 */

import { Controller, Post, Get, Body, Query, Req, Res, Headers } from '@nestjs/common'
import { FastifyRequest, FastifyReply } from 'fastify'
import { ChannelService } from './channel.service'
import { Public } from '../../guards/jwt-auth.guard'

@Controller({ path: '/', version: undefined })
export class ChannelController {
  constructor(private readonly channelService: ChannelService) {}

  // ── 微信公众号 ──

  @Public()
  @Get('webhook/wechat')
  async wechatVerify(
    @Query('signature') signature: string,
    @Query('timestamp') timestamp: string,
    @Query('nonce') nonce: string,
    @Query('echostr') echostr: string,
  ) {
    const adapter = this.channelService.getAdapter('wechat')
    if (adapter?.verifySignature({}, { signature, timestamp, nonce })) {
      return echostr
    }
    return 'verification failed'
  }

  @Public()
  @Post('webhook/wechat')
  async wechatWebhook(@Body() body: unknown, @Res() reply: FastifyReply) {
    const result = await this.channelService.handleInbound('wechat', body)
    if (result) {
      reply.header('Content-Type', 'application/xml')
      return reply.send(result)
    }
    return reply.send('success')
  }

  // ── 企业微信 ──

  @Public()
  @Get('webhook/wecom')
  async wecomVerify(
    @Query('msg_signature') msgSignature: string,
    @Query('timestamp') timestamp: string,
    @Query('nonce') nonce: string,
    @Query('echostr') echostr: string,
  ) {
    const adapter = this.channelService.getAdapter('wecom')
    if (adapter?.verifySignature({}, { msg_signature: msgSignature, timestamp, nonce })) {
      return echostr
    }
    return 'verification failed'
  }

  @Public()
  @Post('webhook/wecom')
  async wecomWebhook(@Body() body: unknown, @Res() reply: FastifyReply) {
    const result = await this.channelService.handleInbound('wecom', body)
    if (result) {
      reply.header('Content-Type', 'application/xml')
      return reply.send(result)
    }
    return reply.send('success')
  }

  // ── Telegram ──

  @Public()
  @Post('webhook/telegram')
  async telegramWebhook(
    @Body() body: unknown,
    @Headers() headers: Record<string, string>,
    @Res() reply: FastifyReply,
  ) {
    const adapter = this.channelService.getAdapter('telegram')
    if (!adapter?.verifySignature(headers, body)) {
      return reply.status(401).send({ error: 'Unauthorized' })
    }

    // Telegram 异步处理，先返回 200
    reply.send({ ok: true })

    // 后台处理消息
    this.channelService.handleInbound('telegram', body).catch((e) => {
      console.error('[Telegram] Handle error:', e)
    })
  }

  // ── Telegram Webhook 设置 ──

  @Public()
  @Post('webhook/telegram/setup')
  async telegramSetup(@Body() body: { url: string }) {
    const adapter = this.channelService.getAdapter('telegram')
    if (!adapter) {
      return { ok: false, error: 'Telegram adapter not available' }
    }
    // TelegramAdapter has setWebhook method
    const tg = adapter as import('./adapters/telegram.adapter').TelegramAdapter
    const ok = await tg.setWebhook(body.url)
    return { ok }
  }

  // ── 账号绑定 ──

  @Public()
  @Post('channels/bind')
  async bindChannelUser(
    @Body() body: { channel: string; channelUserId: string; targetUserId: string },
  ) {
    if (!body.channel || !body.channelUserId || !body.targetUserId) {
      return { ok: false, error: 'channel, channelUserId, targetUserId are required' }
    }
    const ok = await this.channelService.bindChannelUser(
      body.channel, body.channelUserId, body.targetUserId,
    )
    return { ok }
  }

  // ── 渠道用户列表 ──

  @Public()
  @Get('channels/users')
  async listChannelUsers(
    @Query('channel') channel?: string,
    @Query('limit') limit?: string,
  ) {
    return this.channelService.listChannelUsers(channel, Number(limit) || 50)
  }

  // ── 状态 ──

  @Public()
  @Get('channels/stats')
  async channelStats() {
    return {
      channels: await this.channelService.getChannelStats(),
    }
  }
}
