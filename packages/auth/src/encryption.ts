/**
 * AES-256-GCM 对称加密 — 消息内容加密存储
 *
 * 使用 Node.js 原生 crypto，零外部依赖
 * 密钥从环境变量 ENCRYPTION_KEY 派生（32 字节 hex）
 * 格式: iv:authTag:ciphertext (全部 hex 编码)
 */

const ALGO = 'aes-256-gcm'
const IV_LENGTH = 12 // GCM 推荐 12 字节
const TAG_LENGTH = 16

function getKey(): Buffer {
  const raw = process.env.ENCRYPTION_KEY
  if (!raw || raw.length < 32) {
    // 开发环境 fallback（生产环境必须配置）
    return Buffer.from('0'.repeat(64), 'hex')
  }
  // 支持 64 位 hex 或原始 32 字节
  if (raw.length === 64 && /^[0-9a-fA-F]+$/.test(raw)) {
    return Buffer.from(raw, 'hex')
  }
  // 取 SHA-256 哈希确保 32 字节
  const { createHash } = require('node:crypto')
  return createHash('sha256').update(raw).digest()
}

/**
 * 加密明文 → iv:tag:ciphertext (hex)
 */
export async function encrypt(plaintext: string): Promise<string> {
  const { createCipheriv, randomBytes } = await import('node:crypto')
  const key = getKey()
  const iv = randomBytes(IV_LENGTH)
  const cipher = createCipheriv(ALGO, key, iv, { authTagLength: TAG_LENGTH })
  const encrypted = Buffer.concat([
    cipher.update(plaintext, 'utf8'),
    cipher.final(),
  ])
  const tag = cipher.getAuthTag()
  return `${iv.toString('hex')}:${tag.toString('hex')}:${encrypted.toString('hex')}`
}

/**
 * 解密 iv:tag:ciphertext (hex) → 明文
 */
export async function decrypt(ciphertext: string): Promise<string> {
  const { createDecipheriv } = await import('node:crypto')
  const parts = ciphertext.split(':')
  if (parts.length !== 3) {
    throw new Error('Invalid ciphertext format')
  }
  const [ivHex, tagHex, dataHex] = parts as [string, string, string]
  const key = getKey()
  const iv = Buffer.from(ivHex, 'hex')
  const tag = Buffer.from(tagHex, 'hex')
  const data = Buffer.from(dataHex, 'hex')
  const decipher = createDecipheriv(ALGO, key, iv, { authTagLength: TAG_LENGTH })
  decipher.setAuthTag(tag)
  const decrypted = Buffer.concat([
    decipher.update(data),
    decipher.final(),
  ])
  return decrypted.toString('utf8')
}

/**
 * 检测字符串是否为加密格式
 */
export function isEncrypted(text: string): boolean {
  const parts = text.split(':')
  if (parts.length !== 3) return false
  const [iv, tag, data] = parts as [string, string, string]
  return iv.length === IV_LENGTH * 2 && tag.length === TAG_LENGTH * 2 && /^[0-9a-f]+$/i.test(data)
}
