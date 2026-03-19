/**
 * 多级缓存策略（第五章 5.6）
 * L1: 进程内 Map（10s TTL）
 * L2: Redis（5min TTL）
 */
import { Injectable } from '@nestjs/common'

@Injectable()
export class MultiLevelCache {
  private l1 = new Map<string, { value: unknown; expires: number }>()

  async get<T>(key: string): Promise<T | null> {
    // L1
    const l1Entry = this.l1.get(key)
    if (l1Entry && l1Entry.expires > Date.now()) {
      return l1Entry.value as T
    }
    this.l1.delete(key)

    // L2: TODO Redis
    return null
  }

  async set(key: string, value: unknown, ttlMs = 10_000) {
    // L1
    this.l1.set(key, { value, expires: Date.now() + ttlMs })
    // L2: TODO Redis
  }

  async invalidate(key: string) {
    this.l1.delete(key)
    // L2: TODO Redis DEL
  }
}
