import { PrismaClient } from '@prisma/client'

const SLOW_QUERY_THRESHOLD_MS = 500

export function enableSlowQueryLogging(prisma: PrismaClient) {
  prisma.$use(async (params, next) => {
    const start = Date.now()
    const result = await next(params)
    const duration = Date.now() - start

    if (duration > SLOW_QUERY_THRESHOLD_MS) {
      console.warn(`[SLOW QUERY] ${params.model}.${params.action} took ${duration}ms`, {
        model: params.model,
        action: params.action,
        duration,
      })
    }

    return result
  })
}
