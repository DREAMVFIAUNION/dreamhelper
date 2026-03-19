import { NestFactory, Reflector } from '@nestjs/core'
import { FastifyAdapter, NestFastifyApplication } from '@nestjs/platform-fastify'
import { AppModule } from './app.module'
import { JwtAuthGuard } from './guards/jwt-auth.guard'
import { LoggingInterceptor } from './interceptors/logging.interceptor'

async function bootstrap() {
  const app = await NestFactory.create<NestFastifyApplication>(
    AppModule,
    new FastifyAdapter({
      logger: process.env.NODE_ENV === 'development',
    }),
  )

  // CORS
  const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',').filter(Boolean)
  app.enableCors({
    origin: !allowedOrigins || allowedOrigins.length === 0 ? true : allowedOrigins,
    credentials: true,
  })

  // 全局 Auth Guard（需 @Public() 装饰器跳过）
  const reflector = app.get(Reflector)
  app.useGlobalGuards(new JwtAuthGuard(reflector))

  // 全局日志拦截器
  app.useGlobalInterceptors(new LoggingInterceptor())

  // 全局前缀
  app.setGlobalPrefix('api/v1')

  const port = process.env.PORT ?? 3001
  await app.listen(port, '0.0.0.0')
  console.log(`🚀 Gateway running on http://localhost:${port}`)
}

bootstrap()
