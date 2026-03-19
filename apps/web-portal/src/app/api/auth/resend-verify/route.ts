import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'
import { createVerifyCode } from '@/lib/auth/verify-tokens'
import { sendVerificationEmail } from '@/lib/auth/email'

// ═══ POST /api/auth/resend-verify ═══

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

    const user = await prisma.user.findUnique({
      where: { id: payload.sub },
      select: { id: true, email: true, emailVerified: true },
    })

    if (!user) {
      return NextResponse.json({ success: false, errors: ['用户不存在'] }, { status: 404 })
    }

    if (user.emailVerified) {
      return NextResponse.json({ success: false, errors: ['邮箱已验证'] }, { status: 400 })
    }

    const result = createVerifyCode(user.id)

    if (!result) {
      return NextResponse.json({ success: false, errors: ['验证码生成失败'] }, { status: 500 })
    }

    if (result.cooldownRemaining > 0) {
      return NextResponse.json(
        { success: false, errors: [`请 ${result.cooldownRemaining} 秒后再试`] },
        { status: 429 },
      )
    }

    // 发送邮件 (dev 模式会 fallback 到控制台输出)
    const emailResult = await sendVerificationEmail(user.email, result.code)

    return NextResponse.json({
      success: true,
      message: '验证码已发送',
      ...(emailResult.devFallback ? { __dev_code: result.code } : {}),
    })
  } catch (error) {
    console.error('resend-verify failed:', error)
    return NextResponse.json({ success: false, errors: ['服务器错误'] }, { status: 500 })
  }
}
