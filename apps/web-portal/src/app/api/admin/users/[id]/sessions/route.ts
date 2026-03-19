import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'

async function verifyAdmin(req: NextRequest): Promise<{ ok: true } | { ok: false; res: NextResponse }> {
  const tokenStr = req.cookies.get('token')?.value
  if (!tokenStr) return { ok: false, res: NextResponse.json({ success: false, error: '未登录' }, { status: 401 }) }
  try {
    const payload = await verifyToken(tokenStr)
    const user = await prisma.user.findUnique({ where: { id: payload.sub }, select: { tierLevel: true } })
    if (!user || user.tierLevel < 9) return { ok: false, res: NextResponse.json({ success: false, error: '无权限' }, { status: 403 }) }
    return { ok: true }
  } catch {
    return { ok: false, res: NextResponse.json({ success: false, error: 'Token 无效' }, { status: 401 }) }
  }
}

// ═══ GET /api/admin/users/[id]/sessions — 用户的聊天会话列表 ═══

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await verifyAdmin(req)
  if (!auth.ok) return auth.res

  const { id } = await params

  try {
    const sessions = await prisma.chatSession.findMany({
      where: { userId: id },
      select: {
        id: true,
        title: true,
        status: true,
        createdAt: true,
        updatedAt: true,
        _count: { select: { messages: true } },
      },
      orderBy: { updatedAt: 'desc' },
      take: 50,
    })

    return NextResponse.json({
      success: true,
      sessions: sessions.map((s) => ({
        id: s.id,
        title: s.title,
        status: s.status,
        messageCount: s._count.messages,
        createdAt: s.createdAt,
        updatedAt: s.updatedAt,
      })),
    })
  } catch (error) {
    console.error('admin user sessions failed:', error)
    return NextResponse.json({ success: false, error: '服务器错误' }, { status: 500 })
  }
}
