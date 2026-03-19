import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'

// DELETE /api/user/chats — 删除当前用户的所有对话
export async function DELETE(req: NextRequest) {
  try {
    const tokenStr = req.cookies.get('token')?.value
    if (!tokenStr) {
      return NextResponse.json({ success: false, error: '未登录' }, { status: 401 })
    }

    let payload: { sub: string }
    try {
      payload = await verifyToken(tokenStr)
    } catch {
      return NextResponse.json({ success: false, error: 'Token 无效' }, { status: 401 })
    }

    const userId = payload.sub

    // 先删除所有消息，再删除会话
    const sessions = await prisma.chatSession.findMany({
      where: { userId },
      select: { id: true },
    })

    const sessionIds = sessions.map((s) => s.id)

    if (sessionIds.length > 0) {
      await prisma.message.deleteMany({
        where: { sessionId: { in: sessionIds } },
      })
      await prisma.chatSession.deleteMany({
        where: { userId },
      })
    }

    return NextResponse.json({
      success: true,
      deleted: sessionIds.length,
    })
  } catch (error) {
    console.error('delete chats failed:', error)
    return NextResponse.json({ success: false, error: '删除失败' }, { status: 500 })
  }
}
