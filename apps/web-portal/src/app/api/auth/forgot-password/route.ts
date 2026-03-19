import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@dreamhelp/database'
import { createResetToken } from '@/lib/auth/reset-tokens'
import { sendPasswordResetEmail } from '@/lib/auth/email'
import { checkRateLimit } from '@/lib/rate-limit'

// ═══ POST /api/auth/forgot-password ═══

export async function POST(req: NextRequest) {
  try {
    let body: { email?: string }
    try {
      body = (await req.json()) as { email?: string }
    } catch {
      return NextResponse.json({ success: false, errors: ['请求格式错误'] }, { status: 400 })
    }

    const email = body.email?.toLowerCase().trim() ?? ''

    if (!email) {
      return NextResponse.json({ success: false, errors: ['请填写邮箱'] }, { status: 400 })
    }

    const ip = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || req.headers.get('x-real-ip') || 'unknown'
    const rl = checkRateLimit(`forgot:${ip}`, { maxRequests: 3, windowMs: 60_000 })
    if (!rl.allowed) {
      return NextResponse.json({ success: false, errors: ['请求过于频繁，请稍后重试'] }, { status: 429 })
    }

    // 无论邮箱是否存在都返回相同提示（防止邮箱枚举）
    const successMsg = '如果该邮箱已注册，重置链接已发送'

    const user = await prisma.user.findUnique({ where: { email } })

    if (!user || user.status === 'banned') {
      // 不透露邮箱是否存在
      return NextResponse.json({ success: true, message: successMsg })
    }

    const { token, code } = createResetToken(user.id)

    // 构建重置链接
    const baseUrl = process.env.NEXT_PUBLIC_APP_URL || (req.headers.get('origin') ?? `${req.nextUrl.protocol}//${req.nextUrl.host}`)
    const resetUrl = `${baseUrl}/reset?token=${token}&code=${code}`

    // 发送重置邮件
    const emailResult = await sendPasswordResetEmail(email, resetUrl)

    // 开发模式 fallback 到控制台时返回 token 便于调试
    const isDev = process.env.NODE_ENV === 'development'

    return NextResponse.json({
      success: true,
      message: successMsg,
      ...(isDev && emailResult.devFallback ? { __dev_token: token, __dev_code: code } : {}),
    })
  } catch (error) {
    console.error('forgot-password failed:', error)
    return NextResponse.json({ success: false, errors: ['服务器错误'] }, { status: 500 })
  }
}
