/**
 * 渠道用户映射服务 — Phase 8: PostgreSQL 持久化 + 内存缓存
 *
 * 将渠道用户 (telegram_123, wechat_openid) 映射到系统用户 (users.id)
 * 首次消息自动创建系统用户 + 映射记录
 *
 * DB 表: channel_user_mappings (Prisma ChannelUserMapping)
 *        users (自动创建渠道用户)
 */

import { Injectable, Logger } from '@nestjs/common'
import { createHash } from 'crypto'
import { prisma } from '@dreamhelp/database'

export interface UserMapping {
  channelType: string
  channelUserId: string
  systemUserId: string
  displayName?: string
  createdAt: Date
  lastActiveAt: Date
}

@Injectable()
export class UserMappingService {
  private readonly logger = new Logger(UserMappingService.name)
  /** 内存热缓存（DB 为 source of truth） */
  private cache: Map<string, UserMapping> = new Map()

  private key(channelType: string, channelUserId: string): string {
    return `${channelType}:${channelUserId}`
  }

  /** 获取或创建系统用户映射（DB 持久化） */
  async getOrCreateMapping(
    channelType: string,
    channelUserId: string,
    displayName?: string,
  ): Promise<UserMapping> {
    const k = this.key(channelType, channelUserId)

    // 1. 检查内存缓存
    const cached = this.cache.get(k)
    if (cached) {
      cached.lastActiveAt = new Date()
      if (displayName && !cached.displayName) {
        cached.displayName = displayName
      }
      return cached
    }

    try {
      // 2. 查询 DB
      const existing = await prisma.channelUserMapping.findUnique({
        where: { channel_channelUserId: { channel: channelType, channelUserId } },
      })

      if (existing) {
        const mapping: UserMapping = {
          channelType: existing.channel,
          channelUserId: existing.channelUserId,
          systemUserId: existing.userId,
          displayName: existing.displayName ?? undefined,
          createdAt: existing.createdAt,
          lastActiveAt: new Date(),
        }
        this.cache.set(k, mapping)
        return mapping
      }

      // 3. 首次见到此渠道用户 — 自动创建系统用户 + 映射
      const idHash = createHash('md5').update(channelUserId).digest('hex').slice(0, 8)
      const channelEmail = `${channelType}_${idHash}@channel.dreamvfia.com`
      const channelUsername = `${channelType}_${idHash}`

      const user = await prisma.user.create({
        data: {
          email: channelEmail,
          username: channelUsername,
          displayName: displayName || `${channelType} 用户`,
          passwordHash: 'CHANNEL_USER_NO_PASSWORD',
          status: 'active',
          metadata: { sourceChannel: channelType, channelUserId },
        },
      })

      await prisma.channelUserMapping.create({
        data: {
          channel: channelType,
          channelUserId,
          userId: user.id,
          displayName: displayName ?? null,
          metadata: {},
        },
      })

      const mapping: UserMapping = {
        channelType,
        channelUserId,
        systemUserId: user.id,
        displayName: displayName ?? undefined,
        createdAt: new Date(),
        lastActiveAt: new Date(),
      }
      this.cache.set(k, mapping)
      this.logger.log(`New channel user: ${k} → ${user.id}`)
      return mapping

    } catch (err: any) {
      // 降级：DB 不可用时使用临时 ID
      this.logger.warn(`DB fallback for ${k}: ${err.message}`)
      const fallback: UserMapping = {
        channelType,
        channelUserId,
        systemUserId: `channel_${channelType}_${channelUserId}`,
        displayName,
        createdAt: new Date(),
        lastActiveAt: new Date(),
      }
      this.cache.set(k, fallback)
      return fallback
    }
  }

  /** 绑定渠道用户到已有系统账号 */
  async bindToUser(
    channelType: string,
    channelUserId: string,
    targetUserId: string,
  ): Promise<boolean> {
    try {
      await prisma.channelUserMapping.upsert({
        where: { channel_channelUserId: { channel: channelType, channelUserId } },
        update: { userId: targetUserId },
        create: {
          channel: channelType,
          channelUserId,
          userId: targetUserId,
          metadata: {},
        },
      })
      // 更新缓存
      const k = this.key(channelType, channelUserId)
      const cached = this.cache.get(k)
      if (cached) cached.systemUserId = targetUserId
      return true
    } catch (err: any) {
      this.logger.error(`Bind failed: ${err.message}`)
      return false
    }
  }

  /** 获取渠道的会话 ID */
  getSessionId(channelType: string, channelUserId: string): string {
    return `${channelType}_${channelUserId}`
  }

  /** 列出渠道用户映射 */
  async listMappings(channelType?: string, limit = 50): Promise<any[]> {
    const where = channelType ? { channel: channelType } : {}
    return prisma.channelUserMapping.findMany({
      where,
      take: limit,
      orderBy: { createdAt: 'desc' },
    })
  }

  /** 获取所有映射统计 */
  async getStats(): Promise<{ total: number; byChannel: Record<string, number> }> {
    try {
      const groups = await prisma.channelUserMapping.groupBy({
        by: ['channel'],
        _count: { id: true },
      })
      const byChannel: Record<string, number> = {}
      let total = 0
      for (const g of groups) {
        byChannel[g.channel] = g._count.id
        total += g._count.id
      }
      return { total, byChannel }
    } catch {
      // Fallback to cache stats
      const byChannel: Record<string, number> = {}
      for (const m of this.cache.values()) {
        byChannel[m.channelType] = (byChannel[m.channelType] || 0) + 1
      }
      return { total: this.cache.size, byChannel }
    }
  }
}
