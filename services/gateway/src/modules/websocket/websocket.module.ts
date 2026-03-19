import { Module } from '@nestjs/common'
import { WsGateway } from './ws.gateway'
import { RedisPubSubService } from '../redis/redis-pubsub.service'

@Module({
  providers: [WsGateway, RedisPubSubService],
  exports: [WsGateway],
})
export class WebSocketModule {}
