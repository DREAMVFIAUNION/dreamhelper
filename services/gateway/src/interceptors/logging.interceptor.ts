import { CallHandler, ExecutionContext, Injectable, NestInterceptor } from '@nestjs/common'
import { Observable, tap } from 'rxjs'

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const request = context.switchToHttp().getRequest()
    const method = request.method as string
    const url = request.url as string
    const start = Date.now()

    return next.handle().pipe(
      tap(() => {
        const elapsed = Date.now() - start
        const statusCode = context.switchToHttp().getResponse().statusCode as number
        console.log(`[Gateway] ${method} ${url} ${statusCode} ${elapsed}ms`)
      }),
    )
  }
}
