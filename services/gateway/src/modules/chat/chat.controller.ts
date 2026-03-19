import { Controller, Post, Body, Get, Param, Res, HttpException, HttpStatus } from '@nestjs/common'
import { FastifyReply } from 'fastify'

const BRAIN_CORE_URL = process.env.BRAIN_CORE_URL || 'http://127.0.0.1:8000'

@Controller('chat')
export class ChatController {
  @Post('sessions')
  async createSession(@Body() body: { agentId: string; userId?: string; title?: string }) {
    // Phase 1: 返回简单 session（Phase 3 接入 Prisma 持久化）
    const sessionId = crypto.randomUUID()
    return {
      id: sessionId,
      agentId: body.agentId,
      userId: body.userId || 'anonymous',
      title: body.title || '新对话',
      createdAt: new Date().toISOString(),
    }
  }

  @Post('completions')
  async chatCompletions(
    @Body() body: { session_id: string; content: string; stream?: boolean; model?: string; system_prompt?: string },
    @Res() reply: FastifyReply,
  ) {
    const stream = body.stream !== false

    if (!stream) {
      // 非流式：直接代理
      const resp = await fetch(`${BRAIN_CORE_URL}/api/v1/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...body, stream: false }),
      })
      const data = await resp.json()
      return reply.send(data)
    }

    // 流式：SSE 透传
    const resp = await fetch(`${BRAIN_CORE_URL}/api/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, stream: true }),
    })

    if (!resp.ok || !resp.body) {
      throw new HttpException('Brain-core unavailable', HttpStatus.BAD_GATEWAY)
    }

    reply.raw.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    })

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        reply.raw.write(decoder.decode(value, { stream: true }))
      }
    } catch (e) {
      console.error('[Chat] Stream proxy error:', e)
    } finally {
      reply.raw.end()
    }
  }

  @Get('sessions/:id/messages')
  async getMessages(@Param('id') sessionId: string) {
    // 从 brain-core 获取会话历史
    try {
      const resp = await fetch(`${BRAIN_CORE_URL}/api/v1/chat/sessions/${sessionId}/history`)
      const data = await resp.json()
      return data
    } catch {
      return { session_id: sessionId, messages: [] }
    }
  }
}
