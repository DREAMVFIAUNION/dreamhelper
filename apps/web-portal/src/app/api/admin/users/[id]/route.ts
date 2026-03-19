import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@dreamhelp/auth'
import { hashPassword } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'

// ═══ 管理员权限校验 ═══

async function verifyAdmin(req: NextRequest): Promise<{ ok: true; userId: string } | { ok: false; res: NextResponse }> {
  const tokenStr = req.cookies.get('token')?.value
  if (!tokenStr) {
    return { ok: false, res: NextResponse.json({ success: false, error: '未登录' }, { status: 401 }) }
  }
  try {
    const payload = await verifyToken(tokenStr)
    const user = await prisma.user.findUnique({ where: { id: payload.sub }, select: { id: true, tierLevel: true } })
    if (!user || user.tierLevel < 9) {
      return { ok: false, res: NextResponse.json({ success: false, error: '无权限' }, { status: 403 }) }
    }
    return { ok: true, userId: user.id }
  } catch {
    return { ok: false, res: NextResponse.json({ success: false, error: 'Token 无效' }, { status: 401 }) }
  }
}

// ═══ GET /api/admin/users/[id] — 单用户完整详情 ═══

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await verifyAdmin(req)
  if (!auth.ok) return auth.res

  const { id } = await params

  try {
    const user = await prisma.user.findUnique({
      where: { id },
      select: {
        id: true,
        email: true,
        username: true,
        displayName: true,
        avatarUrl: true,
        status: true,
        tierLevel: true,
        emailVerified: true,
        twoFactorEnabled: true,
        lastLoginAt: true,
        metadata: true,
        settings: true,
        createdAt: true,
        updatedAt: true,
      },
    })

    if (!user) {
      return NextResponse.json({ success: false, error: '用户不存在' }, { status: 404 })
    }

    // 统计数据
    const [sessionCount, messageCount, memoryCount] = await Promise.all([
      prisma.chatSession.count({ where: { userId: id } }),
      prisma.message.count({
        where: { session: { userId: id } },
      }),
      prisma.userMemory.count({ where: { userId: id } }),
    ])

    return NextResponse.json({
      success: true,
      user: {
        ...user,
        stats: {
          sessions: sessionCount,
          messages: messageCount,
          memories: memoryCount,
        },
      },
    })
  } catch (error) {
    console.error('admin user detail failed:', error)
    return NextResponse.json({ success: false, error: '服务器错误' }, { status: 500 })
  }
}

// ═══ PUT /api/admin/users/[id] — 编辑用户资料 ═══

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await verifyAdmin(req)
  if (!auth.ok) return auth.res

  const { id } = await params

  try {
    const body = (await req.json()) as {
      displayName?: string
      username?: string
      tierLevel?: number
      status?: string
      emailVerified?: boolean
      resetPassword?: string
    }

    const existing = await prisma.user.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ success: false, error: '用户不存在' }, { status: 404 })
    }

    const updates: Record<string, unknown> = {}

    if (body.displayName !== undefined) updates.displayName = body.displayName
    if (body.username !== undefined) updates.username = body.username
    if (body.tierLevel !== undefined && body.tierLevel >= 0 && body.tierLevel <= 10) {
      updates.tierLevel = body.tierLevel
    }
    if (body.status && ['active', 'locked', 'banned'].includes(body.status)) {
      updates.status = body.status
      if (body.status === 'active') {
        const meta = (existing.metadata as Record<string, unknown>) || {}
        updates.metadata = { ...meta, failedAttempts: 0 }
      }
    }
    if (body.emailVerified !== undefined) updates.emailVerified = body.emailVerified
    if (body.resetPassword) {
      updates.passwordHash = await hashPassword(body.resetPassword)
    }

    const updated = await prisma.user.update({
      where: { id },
      data: updates,
      select: {
        id: true,
        email: true,
        username: true,
        displayName: true,
        status: true,
        tierLevel: true,
        emailVerified: true,
      },
    })

    return NextResponse.json({ success: true, user: updated })
  } catch (error) {
    console.error('admin user update failed:', error)
    return NextResponse.json({ success: false, error: '服务器错误' }, { status: 500 })
  }
}
