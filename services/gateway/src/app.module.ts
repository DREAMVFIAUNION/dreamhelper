import { Module } from '@nestjs/common'
import { ThrottlerModule, ThrottlerGuard } from '@nestjs/throttler'
import { APP_GUARD } from '@nestjs/core'
import { WebSocketModule } from './modules/websocket/websocket.module'
import { ChatModule } from './modules/chat/chat.module'
import { ChannelModule } from './modules/channels/channel.module'
import { HealthController } from './health.controller'

@Module({
  imports: [
    ThrottlerModule.forRoot([{
      ttl: 60_000,   // 1 分钟窗口
      limit: 120,    // 每窗口 120 次
    }]),
    WebSocketModule,
    ChatModule,
    ChannelModule,
  ],
  controllers: [HealthController],
  providers: [
    { provide: APP_GUARD, useClass: ThrottlerGuard },
  ],
})
export class AppModule {}
