import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient | undefined }

/**
 * Prisma 连接池调优:
 * - 开发环境: connection_limit=5, 详细日志
 * - 生产环境: connection_limit=20, pool_timeout=10, 仅 warn+error
 * 参数通过 DATABASE_URL query string 传递给 Prisma Engine
 */
function buildDatasourceUrl(): string | undefined {
  const raw = process.env.DATABASE_URL
  if (!raw) return undefined
  const isProd = process.env.NODE_ENV === 'production'
  const sep = raw.includes('?') ? '&' : '?'
  const poolParams = isProd
    ? `connection_limit=20&pool_timeout=10`
    : `connection_limit=5`
  return `${raw}${sep}${poolParams}`
}

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log:
      process.env.NODE_ENV === 'development'
        ? ['query', 'info', 'warn', 'error']
        : ['warn', 'error'],
    ...(process.env.DATABASE_URL
      ? { datasources: { db: { url: buildDatasourceUrl() } } }
      : {}),
  })

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma
}
