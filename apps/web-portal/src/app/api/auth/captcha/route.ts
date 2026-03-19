import { NextRequest, NextResponse } from 'next/server'
import { buildCaptchaSvg, createCaptcha, issueCaptchaVerifyToken } from '@/lib/auth/captcha'

interface CaptchaVerifyBody {
  captchaId?: string
  answer?: string
}

export async function GET() {
  const { captchaId, answer } = createCaptcha()

  return NextResponse.json({
    captchaId,
    svg: buildCaptchaSvg(answer),
    ...(process.env.NODE_ENV !== 'production' ? { __test_answer: answer } : {}),
  })
}

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as CaptchaVerifyBody
    const captchaId = body.captchaId?.trim() ?? ''
    const answer = body.answer?.trim() ?? ''

    if (!captchaId || !answer) {
      return NextResponse.json({ valid: false, error: '验证码参数不完整' }, { status: 400 })
    }

    const verifyToken = issueCaptchaVerifyToken(captchaId, answer)
    if (!verifyToken) {
      return NextResponse.json({ valid: false, error: '验证码错误或已过期' }, { status: 400 })
    }

    return NextResponse.json({ valid: true, verifyToken })
  } catch {
    return NextResponse.json({ valid: false, error: '请求格式错误' }, { status: 400 })
  }
}
