import { Module } from '@nestjs/common'
import { ChatController } from './chat.controller'
import { MessagePersistenceService } from './message-persistence.service'

@Module({
  controllers: [ChatController],
  providers: [MessagePersistenceService],
})
export class ChatModule {}
