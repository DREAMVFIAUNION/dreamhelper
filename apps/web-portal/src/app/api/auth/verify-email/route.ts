import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'
import { consumeVerifyCode } from '@/lib/auth/verify-tokens'

interface VerifyBody {
  code?: string
}

// ═══ POST /api/auth/verify-email ═══

export async function POST(req: NextRequest) {
  try {
    const tokenStr = req.cookies.get('token')?.value
    if (!tokenStr) {
      return NextResponse.json({ success: false, errors: ['未登录'] }, { status: 401 })
    }

    let payload: { sub: string }
    try {
      payload = await verifyToken(tokenStr)
    } catch {
      return NextResponse.json({ success: false, errors: ['Token 无效'] }, { status: 401 })
    }

    let body: VerifyBody
    try {
      body = (await req.json()) as VerifyBody
    } catch {
      return NextResponse.json({ success: false, errors: ['请求格式错误'] }, { status: 400 })
    }

    const code = body.code?.trim() ?? ''

    if (!code || code.length !== 6) {
      return NextResponse.json({ success: false, errors: ['请输入 6 位验证码'] }, { status: 400 })
    }

    const valid = consumeVerifyCode(payload.sub, code)
    if (!valid) {
      return NextResponse.json({ success: false, errors: ['验证码错误或已过期'] }, { status: 400 })
    }

    await prisma.user.update({
      where: { id: payload.sub },
      data: { emailVerified: true },
    })

    return NextResponse.json({
      success: true,
      message: '邮箱验证成功',
    })
  } catch (error) {
    console.error('verify-email failed:', error)
    return NextResponse.json({ success: false, errors: ['服务器错误'] }, { status: 500 })
  }
}
