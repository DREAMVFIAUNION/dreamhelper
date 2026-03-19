import { Controller, Get } from '@nestjs/common'
import { Public } from './guards/jwt-auth.guard'

@Controller('health')
export class HealthController {
  @Public()
  @Get()
  check() {
    return { status: 'ok', service: 'gateway', version: '3.0.0', timestamp: new Date().toISOString() }
  }
}
