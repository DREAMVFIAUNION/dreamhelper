import { NextRequest, NextResponse } from 'next/server'
import { signToken, verifyPassword } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'

interface LoginBody {
  email?: string
  password?: string
}

interface RateLimitRecord {
  count: number
  resetAt: number
}

const WINDOW_MS = 60_000
const MAX_ATTEMPTS_PER_WINDOW = 5
const ACCOUNT_LOCK_THRESHOLD = 5

const loginAttempts = new Map<string, RateLimitRecord>()

function checkRateLimit(ip: string): boolean {
  const now = Date.now()
  const record = loginAttempts.get(ip)

  if (!record || now > record.resetAt) {
    loginAttempts.set(ip, { count: 1, resetAt: now + WINDOW_MS })
    return true
  }

  record.count += 1
  return record.count <= MAX_ATTEMPTS_PER_WINDOW
}

export async function POST(req: NextRequest) {
  try {
    let body: LoginBody
    try {
      body = (await req.json()) as LoginBody
    } catch {
      return NextResponse.json({ success: false, errors: ['请求格式错误'] }, { status: 400 })
    }
    const email = body.email?.toLowerCase().trim() ?? ''
    const password = body.password ?? ''

    if (!email || !password) {
      return NextResponse.json({ success: false, errors: ['请填写邮箱和密码'] }, { status: 400 })
    }

    const ip = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || req.headers.get('x-real-ip') || 'unknown'

    if (!checkRateLimit(ip)) {
      return NextResponse.json(
        { success: false, errors: ['登录尝试过于频繁，请 1 分钟后重试'] },
        { status: 429 },
      )
    }

    const user = await prisma.user.findUnique({ where: { email } })
    if (!user) {
      return NextResponse.json({ success: false, errors: ['邮箱或密码错误'] }, { status: 401 })
    }

    if (user.status === 'banned') {
      return NextResponse.json({ success: false, errors: ['该账号已被禁用，请联系客服'] }, { status: 403 })
    }
    if (user.status === 'locked') {
      return NextResponse.json({ success: false, errors: ['该账号已被锁定，请稍后重试'] }, { status: 403 })
    }

    const isValid = await verifyPassword(password, user.passwordHash)

    const currentMeta = ((user.metadata as Record<string, unknown> | null) ?? {}) as Record<string, unknown>
    const currentFailedAttempts = Number(currentMeta.failedAttempts ?? 0)

    if (!isValid) {
      const nextFailedAttempts = currentFailedAttempts + 1

      if (nextFailedAttempts >= ACCOUNT_LOCK_THRESHOLD) {
        await prisma.user.update({
          where: { id: user.id },
          data: {
            status: 'locked',
            metadata: {
              ...currentMeta,
              failedAttempts: nextFailedAttempts,
              lockedAt: new Date().toISOString(),
            },
          },
        })

        return NextResponse.json({ success: false, errors: ['密码错误次数过多，账号已临时锁定'] }, { status: 403 })
      }

      await prisma.user.update({
        where: { id: user.id },
        data: {
          metadata: {
            ...currentMeta,
            failedAttempts: nextFailedAttempts,
          },
        },
      })

      return NextResponse.json({ success: false, errors: ['邮箱或密码错误'] }, { status: 401 })
    }

    const role = user.tierLevel >= 9 ? 'admin' : user.tierLevel >= 2 ? 'enterprise' : user.tierLevel >= 1 ? 'vip' : 'user'

    const token = await signToken({
      sub: user.id,
      email: user.email,
      role,
    })

    await prisma.user.update({
      where: { id: user.id },
      data: {
        lastLoginAt: new Date(),
        metadata: {
          ...currentMeta,
          failedAttempts: 0,
          lastLoginIp: ip,
          lastLoginAt: new Date().toISOString(),
        },
      },
    })

    const response = NextResponse.json({
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
    })

    response.cookies.set('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 60 * 60 * 24 * 7,
      path: '/',
    })

    return response
  } catch (error) {
    console.error('login failed:', error)
    return NextResponse.json({ success: false, errors: ['服务器错误'] }, { status: 500 })
  }
}
