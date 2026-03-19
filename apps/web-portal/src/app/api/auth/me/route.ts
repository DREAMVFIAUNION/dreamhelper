import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'

export async function GET(req: NextRequest) {
  try {
    const token = req.cookies.get('token')?.value
    if (!token) {
      return NextResponse.json({ success: false, error: '未登录' }, { status: 401 })
    }

    const payload = await verifyToken(token)

    const user = await prisma.user.findUnique({
      where: { id: payload.sub },
      select: {
        id: true,
        email: true,
        username: true,
        displayName: true,
        avatarUrl: true,
        tierLevel: true,
        emailVerified: true,
        status: true,
        settings: true,
        createdAt: true,
      },
    })

    if (!user || user.status !== 'active') {
      const res = NextResponse.json({ success: false, error: '用户不存在或已禁用' }, { status: 401 })
      res.cookies.delete('token')
      return res
    }

    return NextResponse.json({ success: true, user })
  } catch {
    const res = NextResponse.json({ success: false, error: 'Token 无效' }, { status: 401 })
    res.cookies.delete('token')
    return res
  }
}
