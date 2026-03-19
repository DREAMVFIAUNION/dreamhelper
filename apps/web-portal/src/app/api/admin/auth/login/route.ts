import { NextRequest, NextResponse } from 'next/server'
import { verifyPassword, signToken } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'

interface AdminLoginBody {
  email?: string
  password?: string
}

// ═══ POST /api/admin/auth/login ═══

export async function POST(req: NextRequest) {
  try {
    let body: AdminLoginBody
    try {
      body = (await req.json()) as AdminLoginBody
    } catch {
      return NextResponse.json({ success: false, errors: ['请求格式错误'] }, { status: 400 })
    }

    const email = body.email?.toLowerCase().trim() ?? ''
    const password = body.password ?? ''

    if (!email || !password) {
      return NextResponse.json(
        { success: false, errors: ['请填写邮箱和密码'] },
        { status: 400 },
      )
    }

    const user = await prisma.user.findUnique({ where: { email } })

    if (!user) {
      return NextResponse.json(
        { success: false, errors: ['邮箱或密码错误'] },
        { status: 401 },
      )
    }

    // 检查管理员权限 (tierLevel >= 9)
    if (user.tierLevel < 9) {
      return NextResponse.json(
        { success: false, errors: ['无管理员权限'] },
        { status: 403 },
      )
    }

    if (user.status !== 'active') {
      return NextResponse.json(
        { success: false, errors: ['账号状态异常'] },
        { status: 403 },
      )
    }

    const isValid = await verifyPassword(password, user.passwordHash)
    if (!isValid) {
      return NextResponse.json(
        { success: false, errors: ['邮箱或密码错误'] },
        { status: 401 },
      )
    }

    // 签发管理员 Token (带 admin role, 有效期更短)
    const meta = (user.metadata as Record<string, unknown>) || {}
    const adminRole = (meta.adminRole as string) || (user.tierLevel >= 10 ? 'super_admin' : 'admin')

    const token = await signToken({
      sub: user.id,
      email: user.email,
      role: adminRole,
    })

    const response = NextResponse.json({
      success: true,
      user: {
        id: user.id,
        email: user.email,
        username: user.username,
        displayName: user.displayName,
        avatarUrl: user.avatarUrl,
        role: adminRole,
      },
    })

    response.cookies.set('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 60 * 60 * 4, // 4 小时（管理员 Token 更短）
      path: '/',
    })

    return response
  } catch (error) {
    console.error('admin login failed:', error)
    return NextResponse.json(
      { success: false, errors: ['服务器错误'] },
      { status: 500 },
    )
  }
}
