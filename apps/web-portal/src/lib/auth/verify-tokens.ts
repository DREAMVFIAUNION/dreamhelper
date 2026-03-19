import { randomInt } from 'node:crypto'

// ═══ 邮箱验证码 Store (生产环境应使用 Redis) ═══

interface VerifyRecord {
  userId: string
  code: string
  expiresAt: number
}

const VERIFY_TTL_MS = 10 * 60 * 1000 // 10 分钟
const COOLDOWN_MS = 60 * 1000 // 60 秒重发冷却

const verifyStore = new Map<string, VerifyRecord>()
const cooldownStore = new Map<string, number>() // userId -> lastSentAt

function cleanExpired() {
  const now = Date.now()
  for (const [key, record] of verifyStore) {
    if (record.expiresAt <= now) verifyStore.delete(key)
  }
  for (const [key, ts] of cooldownStore) {
    if (now - ts > COOLDOWN_MS) cooldownStore.delete(key)
  }
}

/** 生成 6 位验证码并存储 */
export function createVerifyCode(userId: string): { code: string; cooldownRemaining: number } | null {
  cleanExpired()

  const lastSent = cooldownStore.get(userId)
  if (lastSent) {
    const remaining = Math.ceil((COOLDOWN_MS - (Date.now() - lastSent)) / 1000)
    if (remaining > 0) {
      return { code: '', cooldownRemaining: remaining }
    }
  }

  // 清除该用户之前的验证码
  for (const [key, record] of verifyStore) {
    if (record.userId === userId) verifyStore.delete(key)
  }

  const code = randomInt(100000, 999999).toString()

  verifyStore.set(`${userId}:${code}`, {
    userId,
    code,
    expiresAt: Date.now() + VERIFY_TTL_MS,
  })

  cooldownStore.set(userId, Date.now())

  return { code, cooldownRemaining: 0 }
}

/** 验证邮箱验证码（一次性） */
export function consumeVerifyCode(userId: string, code: string): boolean {
  cleanExpired()

  const key = `${userId}:${code}`
  const record = verifyStore.get(key)
  if (!record) return false

  verifyStore.delete(key)
  if (Date.now() > record.expiresAt) return false
  return record.userId === userId
}
