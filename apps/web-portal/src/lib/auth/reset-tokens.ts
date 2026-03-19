import { randomBytes, randomInt } from 'node:crypto'

// ═══ 内存 Reset Token Store (生产环境应使用 Redis) ═══

interface ResetRecord {
  userId: string
  code: string
  expiresAt: number
}

const RESET_TTL_MS = 30 * 60 * 1000 // 30 分钟
const resetTokenStore = new Map<string, ResetRecord>()

function cleanExpired() {
  const now = Date.now()
  for (const [key, record] of resetTokenStore) {
    if (record.expiresAt <= now) resetTokenStore.delete(key)
  }
}

/** 创建重置 token + 6位验证码 */
export function createResetToken(userId: string): { token: string; code: string } {
  cleanExpired()

  const token = randomBytes(32).toString('hex')
  const code = randomInt(100000, 999999).toString()

  resetTokenStore.set(token, {
    userId,
    code,
    expiresAt: Date.now() + RESET_TTL_MS,
  })

  return { token, code }
}

/** 消费重置 token（一次性） */
export function consumeResetToken(token: string): { userId: string } | null {
  cleanExpired()
  const record = resetTokenStore.get(token)
  if (!record) return null
  resetTokenStore.delete(token)
  if (Date.now() > record.expiresAt) return null
  return { userId: record.userId }
}
