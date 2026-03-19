const ITERATIONS = 100_000
const KEY_LENGTH = 64
const DIGEST = 'sha512'

export async function hashPassword(password: string): Promise<string> {
  const { pbkdf2, randomBytes } = await import('node:crypto')
  const { promisify } = await import('node:util')
  const pbkdf2Async = promisify(pbkdf2)

  const salt = randomBytes(32).toString('hex')
  const hash = await pbkdf2Async(password, salt, ITERATIONS, KEY_LENGTH, DIGEST)
  return `${salt}:${hash.toString('hex')}`
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const { pbkdf2 } = await import('node:crypto')
  const { promisify } = await import('node:util')
  const pbkdf2Async = promisify(pbkdf2)

  const [salt, hash] = stored.split(':')
  if (!salt || !hash) return false
  const verify = await pbkdf2Async(password, salt, ITERATIONS, KEY_LENGTH, DIGEST)
  return verify.toString('hex') === hash
}
