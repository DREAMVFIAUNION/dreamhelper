import { NextRequest, NextResponse } from 'next/server'
import { hashPassword, verifyPassword, verifyToken } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'

const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/

interface ChangePasswordBody {
  currentPassword?: string
  newPassword?: string
}

// ═══ PUT /api/auth/password — 修改密码（需登录） ═══

export async function PUT(req: NextRequest) {
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

    let body: ChangePasswordBody
    try {
      body = (await req.json()) as ChangePasswordBody
    } catch {
      return NextResponse.json({ success: false, errors: ['请求格式错误'] }, { status: 400 })
    }

    const currentPassword = body.currentPassword ?? ''
    const newPassword = body.newPassword ?? ''

    if (!currentPassword || !newPassword) {
      return NextResponse.json({ success: false, errors: ['请填写当前密码和新密码'] }, { status: 400 })
    }

    if (!PASSWORD_REGEX.test(newPassword)) {
      return NextResponse.json(
        { success: false, errors: ['新密码至少 8 位，且需包含大小写字母和数字'] },
        { status: 400 },
      )
    }

    const user = await prisma.user.findUnique({ where: { id: payload.sub } })
    if (!user) {
      return NextResponse.json({ success: false, errors: ['用户不存在'] }, { status: 404 })
    }

    const isValid = await verifyPassword(currentPassword, user.passwordHash)
    if (!isValid) {
      return NextResponse.json({ success: false, errors: ['当前密码错误'] }, { status: 401 })
    }

    const passwordHash = await hashPassword(newPassword)

    await prisma.user.update({
      where: { id: user.id },
      data: { passwordHash },
    })

    return NextResponse.json({
      success: true,
      message: '密码修改成功',
    })
  } catch (error) {
    console.error('change-password failed:', error)
    return NextResponse.json({ success: false, errors: ['服务器错误'] }, { status: 500 })
  }
}
