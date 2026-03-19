/**
 * WebSocket 网关（第四章 4.4）
 * 支持: 用户连接管理, 会话加入, 主动唤醒推送, Redis Pub/Sub 集成
 */
import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayConnection,
  OnGatewayDisconnect,
  OnGatewayInit,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets'
import { Inject, forwardRef } from '@nestjs/common'
import { Server, Socket } from 'socket.io'
import { RedisPubSubService } from '../redis/redis-pubsub.service'

@WebSocketGateway({
  cors: { origin: '*' },
  namespace: '/ws',
})
export class WsGateway implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server!: Server

  private connections = new Map<string, Socket>()
  private onlineUsers = new Set<string>()

  constructor(
    @Inject(forwardRef(() => RedisPubSubService))
    private readonly redisPubSub: RedisPubSubService,
  ) {}

  async afterInit() {
    // 订阅主动唤醒频道
    await this.redisPubSub.subscribe('proactive:notify', (message: string) => {
      try {
        const data = JSON.parse(message) as { userId: string; type: string; title: string; content: string }
        this.notifyUser(data.userId, 'proactive:message', {
          type: data.type,
          title: data.title,
          content: data.content,
          timestamp: Date.now(),
        })
      } catch (err) {
        console.error('[WS] Failed to parse proactive message:', err)
      }
    })

    // 订阅通用通知频道
    await this.redisPubSub.subscribe('notification:push', (message: string) => {
      try {
        const data = JSON.parse(message) as { userId: string; event: string; payload: unknown }
        this.notifyUser(data.userId, data.event, data.payload)
      } catch (err) {
        console.error('[WS] Failed to parse notification:', err)
      }
    })

    // 订阅工作流执行状态频道（模式匹配）
    await this.redisPubSub.psubscribe('workflow:execution:*', (message: string, channel: string) => {
      try {
        const data = JSON.parse(message) as { executionId: string; event: string; [k: string]: unknown }
        // 广播给订阅了该执行的 room
        this.server.to(`workflow:${data.executionId}`).emit('workflow:status', data)
      } catch (err) {
        console.error('[WS] Failed to parse workflow execution event:', err)
      }
    })

    console.log(`[WS] Gateway initialized, listening for Redis events`)
  }

  handleConnection(client: Socket) {
    const userId = client.handshake.query['userId'] as string
    if (userId) {
      this.connections.set(userId, client)
      this.onlineUsers.add(userId)
      client.join(`user:${userId}`)
    }
    console.log(`[WS] Connected: ${client.id} (user: ${userId ?? 'anonymous'}) — Online: ${this.onlineUsers.size}`)
  }

  handleDisconnect(client: Socket) {
    const userId = client.handshake.query['userId'] as string
    if (userId) {
      this.connections.delete(userId)
      this.onlineUsers.delete(userId)
    }
    console.log(`[WS] Disconnected: ${client.id} — Online: ${this.onlineUsers.size}`)
  }

  @SubscribeMessage('chat:join')
  handleJoinSession(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { sessionId: string },
  ) {
    client.join(`session:${data.sessionId}`)
    return { event: 'chat:joined', data: { sessionId: data.sessionId } }
  }

  @SubscribeMessage('heartbeat')
  handleHeartbeat(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { userId: string },
  ) {
    if (data.userId) this.onlineUsers.add(data.userId)
    return { event: 'heartbeat:ack', data: { timestamp: Date.now() } }
  }

  @SubscribeMessage('workflow:subscribe')
  handleWorkflowSubscribe(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { executionId: string },
  ) {
    if (data.executionId) {
      client.join(`workflow:${data.executionId}`)
    }
    return { event: 'workflow:subscribed', data: { executionId: data.executionId } }
  }

  @SubscribeMessage('ping')
  handlePing() {
    return { event: 'pong', data: { timestamp: Date.now() } }
  }

  /** 向指定用户推送通知 */
  notifyUser(userId: string, event: string, data: unknown) {
    this.server.to(`user:${userId}`).emit(event, data)
  }

  /** 向指定会话推送消息 */
  broadcastToSession(sessionId: string, event: string, data: unknown) {
    this.server.to(`session:${sessionId}`).emit(event, data)
  }

  /** 获取在线用户数 */
  getOnlineCount(): number {
    return this.onlineUsers.size
  }
}
