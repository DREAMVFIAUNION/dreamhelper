/**
 * Redis Pub/Sub 跨节点广播（第四章 4.5）
 */
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common'
import { createClient, type RedisClientType } from 'redis'

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379'

@Injectable()
export class RedisPubSubService implements OnModuleInit, OnModuleDestroy {
  private publisher!: RedisClientType
  private subscriber!: RedisClientType
  private handlers = new Map<string, (message: string) => void>()

  async onModuleInit() {
    try {
      this.publisher = createClient({ url: REDIS_URL }) as RedisClientType
      this.subscriber = this.publisher.duplicate() as RedisClientType

      await this.publisher.connect()
      await this.subscriber.connect()
      console.log('[Redis PubSub] Connected to', REDIS_URL)
    } catch (err) {
      console.warn('[Redis PubSub] Connection failed, running in local-only mode:', (err as Error).message)
    }
  }

  async publish(channel: string, message: string) {
    try {
      if (this.publisher?.isReady) {
        await this.publisher.publish(channel, message)
      }
    } catch (err) {
      console.error('[Redis PubSub] Publish error:', (err as Error).message)
    }
  }

  async subscribe(channel: string, handler: (message: string) => void) {
    this.handlers.set(channel, handler)
    try {
      if (this.subscriber?.isReady) {
        await this.subscriber.subscribe(channel, (message) => {
          handler(message)
        })
        console.log(`[Redis PubSub] Subscribed to ${channel}`)
      }
    } catch (err) {
      console.error('[Redis PubSub] Subscribe error:', (err as Error).message)
    }
  }

  async psubscribe(pattern: string, handler: (message: string, channel: string) => void) {
    try {
      if (this.subscriber?.isReady) {
        await this.subscriber.pSubscribe(pattern, (message, channel) => {
          handler(message, channel)
        })
        console.log(`[Redis PubSub] Pattern-subscribed to ${pattern}`)
      }
    } catch (err) {
      console.error('[Redis PubSub] PSubscribe error:', (err as Error).message)
    }
  }

  async onModuleDestroy() {
    try {
      await this.subscriber?.quit()
      await this.publisher?.quit()
    } catch {}
  }
}
