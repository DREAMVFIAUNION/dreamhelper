import { NextRequest, NextResponse } from 'next/server'
import { hashPassword } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'
import { consumeResetToken } from '@/lib/auth/reset-tokens'

const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/

interface ResetBody {
  token?: string
  password?: string
}

// ═══ POST /api/auth/reset-password ═══

export async function POST(req: NextRequest) {
  try {
    let body: ResetBody
    try {
      body = (await req.json()) as ResetBody
    } catch {
      return NextResponse.json({ success: false, errors: ['请求格式错误'] }, { status: 400 })
    }

    const token = body.token?.trim() ?? ''
    const password = body.password ?? ''

    if (!token) {
      return NextResponse.json({ success: false, errors: ['重置令牌缺失'] }, { status: 400 })
    }

    if (!PASSWORD_REGEX.test(password)) {
      return NextResponse.json(
        { success: false, errors: ['密码至少 8 位，且需包含大小写字母和数字'] },
        { status: 400 },
      )
    }

    const result = consumeResetToken(token)
    if (!result) {
      return NextResponse.json(
        { success: false, errors: ['重置链接无效或已过期，请重新申请'] },
        { status: 400 },
      )
    }

    const passwordHash = await hashPassword(password)

    await prisma.user.update({
      where: { id: result.userId },
      data: {
        passwordHash,
        status: 'active', // 解锁账号（如果之前被锁定）
        metadata: {
          failedAttempts: 0,
        },
      },
    })

    return NextResponse.json({
      success: true,
      message: '密码重置成功，请使用新密码登录',
    })
  } catch (error) {
    console.error('reset-password failed:', error)
    return NextResponse.json({ success: false, errors: ['服务器错误'] }, { status: 500 })
  }
}
