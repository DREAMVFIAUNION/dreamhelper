import { PrismaClient } from '@prisma/client'

function createPrismaClient(url?: string) {
  if (url) {
    return new PrismaClient({
      datasources: { db: { url } },
    })
  }

  return new PrismaClient()
}

export const writePrisma = createPrismaClient(process.env.DATABASE_URL)

export const readPrisma = createPrismaClient(process.env.DATABASE_READ_URL ?? process.env.DATABASE_URL)
