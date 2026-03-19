/**
 * 消息持久化与断点续传（第四章 4.8）
 */
import { Injectable } from '@nestjs/common'

@Injectable()
export class MessagePersistenceService {
  async saveMessage(sessionId: string, role: string, content: string) {
    // TODO: 接入 Prisma 持久化
    console.log(`[Persist] ${sessionId} ${role}: ${content.slice(0, 50)}...`)
  }

  async getStreamBuffer(sessionId: string): Promise<string | null> {
    // TODO: 从 Redis 获取流式缓冲
    return null
  }

  async setStreamBuffer(sessionId: string, buffer: string) {
    // TODO: 写入 Redis 流式缓冲
  }

  async clearStreamBuffer(sessionId: string) {
    // TODO: 清除 Redis 流式缓冲
  }
}
