import { Module } from '@nestjs/common'
import { ChannelController } from './channel.controller'
import { ChannelService } from './channel.service'
import { UserMappingService } from './user-mapping.service'

@Module({
  controllers: [ChannelController],
  providers: [ChannelService, UserMappingService],
  exports: [ChannelService, UserMappingService],
})
export class ChannelModule {}
