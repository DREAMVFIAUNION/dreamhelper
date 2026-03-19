import { NextRequest, NextResponse } from 'next/server'
import { hashPassword, signToken } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'
import { consumeCaptchaVerifyToken } from '@/lib/auth/captcha'
import { checkRateLimit } from '@/lib/rate-limit'

const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
const USERNAME_REGEX = /^[a-zA-Z0-9_\u4e00-\u9fa5]{2,20}$/
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/

interface RegisterBody {
  email?: string
  username?: string
  password?: string
  captchaVerifyToken?: string
}

function generateDefaultAvatar(username: string): string {
  let hash = 0
  for (const char of username) {
    hash = char.charCodeAt(0) + ((hash << 5) - hash)
  }

  const hue = Math.abs(hash) % 360
  const initial = username.charAt(0).toUpperCase() || 'U'

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><rect width="128" height="128" fill="hsl(${hue},60%,30%)"/><text x="64" y="72" font-size="48" font-family="sans-serif" fill="hsl(${hue},80%,80%)" text-anchor="middle" dominant-baseline="middle">${initial}</text></svg>`

  return `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`
}

export async function POST(req: NextRequest) {
  try {
    let body: RegisterBody
    try {
      body = (await req.json()) as RegisterBody
    } catch {
      return NextResponse.json({ success: false, errors: ['请求格式错误'] }, { status: 400 })
    }

    const email = body.email?.toLowerCase().trim() ?? ''
    const username = body.username?.trim() ?? ''
    const password = body.password ?? ''
    const captchaVerifyToken = body.captchaVerifyToken ?? ''

    const ip = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || req.headers.get('x-real-ip') || 'unknown'
    const rl = checkRateLimit(`register:${ip}`, { maxRequests: 5, windowMs: 60_000 })
    if (!rl.allowed) {
      return NextResponse.json({ success: false, errors: ['注册请求过于频繁，请稍后重试'] }, { status: 429 })
    }

    const errors: string[] = []

    if (!EMAIL_REGEX.test(email)) {
      errors.push('邮箱格式不正确')
    }
    if (!USERNAME_REGEX.test(username)) {
      errors.push('用户名需 2-20 位，支持字母、数字、下划线、中文')
    }
    if (!PASSWORD_REGEX.test(password)) {
      errors.push('密码至少 8 位，且需包含大小写字母和数字')
    }

    if (!captchaVerifyToken) {
      errors.push('验证码校验令牌缺失')
    } else if (!consumeCaptchaVerifyToken(captchaVerifyToken)) {
      errors.push('验证码无效或已过期')
    }

    if (errors.length > 0) {
      return NextResponse.json({ success: false, errors }, { status: 400 })
    }

    const existingEmail = await prisma.user.findUnique({ where: { email } })
    if (existingEmail) {
      return NextResponse.json({ success: false, errors: ['该邮箱已注册'] }, { status: 409 })
    }

    const existingUsername = await prisma.user.findUnique({ where: { username } })
    if (existingUsername) {
      return NextResponse.json({ success: false, errors: ['该用户名已被占用'] }, { status: 409 })
    }

    const passwordHash = await hashPassword(password)

    const user = await prisma.user.create({
      data: {
        email,
        username,
        passwordHash,
        displayName: username,
        avatarUrl: generateDefaultAvatar(username),
        status: 'active',
        tierLevel: 0,
        emailVerified: false,
        metadata: { failedAttempts: 0 },
        settings: { theme: 'dark', language: 'zh-CN' },
      },
    })

    const token = await signToken({
      sub: user.id,
      email: user.email,
      role: 'user',
    })

    const response = NextResponse.json(
      {
        success: true,
        user: {
          id: user.id,
          email: user.email,
          username: user.username,
          displayName: user.displayName,
          avatarUrl: user.avatarUrl,
          tierLevel: user.tierLevel,
          emailVerified: user.emailVerified,
        },
      },
      { status: 201 },
    )

    response.cookies.set('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 60 * 60 * 24 * 7,
      path: '/',
    })

    return response
  } catch (error) {
    console.error('register failed:', error)
    return NextResponse.json({ success: false, errors: ['服务器错误，请稍后重试'] }, { status: 500 })
  }
}
