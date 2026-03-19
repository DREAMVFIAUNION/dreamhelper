import { createHash, randomBytes, randomInt } from 'node:crypto'

interface CaptchaRecord {
  answer: string
  expiresAt: number
}

const CAPTCHA_TTL_MS = 5 * 60 * 1000
const CAPTCHA_VERIFY_TOKEN_TTL_MS = 10 * 60 * 1000

const captchaStore = new Map<string, CaptchaRecord>()
const verifyTokenStore = new Map<string, number>()

function cleanExpired() {
  const now = Date.now()

  for (const [key, value] of captchaStore) {
    if (value.expiresAt <= now) captchaStore.delete(key)
  }

  for (const [token, expiresAt] of verifyTokenStore) {
    if (expiresAt <= now) verifyTokenStore.delete(token)
  }
}

export function createCaptcha(): { captchaId: string; answer: string } {
  cleanExpired()

  const answer = randomInt(1000, 9999).toString()
  const captchaId = randomBytes(16).toString('hex')

  captchaStore.set(captchaId, {
    answer,
    expiresAt: Date.now() + CAPTCHA_TTL_MS,
  })

  return { captchaId, answer }
}

export function verifyCaptchaAnswer(captchaId: string, answer: string): boolean {
  cleanExpired()

  const record = captchaStore.get(captchaId)
  if (!record) return false

  captchaStore.delete(captchaId)
  if (Date.now() > record.expiresAt) return false

  return record.answer === answer
}

export function issueCaptchaVerifyToken(captchaId: string, answer: string): string | null {
  const valid = verifyCaptchaAnswer(captchaId, answer)
  if (!valid) return null

  const verifyToken = createHash('sha256')
    .update(`${captchaId}:${answer}:${Date.now()}:${randomBytes(8).toString('hex')}`)
    .digest('hex')

  verifyTokenStore.set(verifyToken, Date.now() + CAPTCHA_VERIFY_TOKEN_TTL_MS)

  return verifyToken
}

export function consumeCaptchaVerifyToken(token: string): boolean {
  cleanExpired()

  const expiresAt = verifyTokenStore.get(token)
  if (!expiresAt) return false

  verifyTokenStore.delete(token)
  return Date.now() <= expiresAt
}

export function buildCaptchaSvg(answer: string): string {
  const width = 150
  const height = 50

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`
  svg += `<rect width="${width}" height="${height}" fill="#1a1a2e"/>`

  for (let i = 0; i < 5; i += 1) {
    const x1 = Math.random() * width
    const y1 = Math.random() * height
    const x2 = Math.random() * width
    const y2 = Math.random() * height
    const hue = Math.random() * 360
    svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="hsl(${hue},50%,40%)" stroke-width="1"/>`
  }

  for (let i = 0; i < 30; i += 1) {
    const cx = Math.random() * width
    const cy = Math.random() * height
    const light = 30 + Math.random() * 30
    svg += `<circle cx="${cx}" cy="${cy}" r="1" fill="hsl(0,0%,${light}%)"/>`
  }

  const chars = answer.split('')
  const charWidth = width / (chars.length + 1)

  chars.forEach((char, i) => {
    const x = charWidth * (i + 0.8) + (Math.random() - 0.5) * 8
    const y = height / 2 + (Math.random() - 0.5) * 10
    const rotate = (Math.random() - 0.5) * 30
    const hue = Math.random() * 60 + 340

    svg += `<text x="${x}" y="${y}" font-size="${22 + Math.random() * 6}" font-family="monospace" fill="hsl(${hue},80%,70%)" transform="rotate(${rotate},${x},${y})" dominant-baseline="central">${char}</text>`
  })

  svg += '</svg>'

  return `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`
}
