import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'
import { brainCoreFetch } from '@/lib/brain-core-url'

// GET /api/knowledge/[id] — 获取单个文档详情
export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
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

    const { id } = await params

    const doc = await prisma.document.findUnique({
      where: { id },
      include: { knowledgeBase: { select: { ownerId: true } } },
    })

    if (!doc || doc.knowledgeBase.ownerId !== payload.sub) {
      return NextResponse.json({ success: false, error: '文档不存在' }, { status: 404 })
    }

    return NextResponse.json({
      success: true,
      document: {
        id: doc.id,
        title: doc.title,
        content: doc.content,
        docType: doc.docType,
        status: doc.status,
        chunkCount: doc.chunkCount,
        createdAt: doc.createdAt,
        updatedAt: doc.updatedAt,
      },
    })
  } catch (error) {
    console.error('knowledge get failed:', error)
    return NextResponse.json({ success: false, error: '服务器错误' }, { status: 500 })
  }
}

// DELETE /api/knowledge/[id] — 删除文档
export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
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

    const { id } = await params

    const doc = await prisma.document.findUnique({
      where: { id },
      include: { knowledgeBase: { select: { id: true, ownerId: true } } },
    })

    if (!doc || doc.knowledgeBase.ownerId !== payload.sub) {
      return NextResponse.json({ success: false, error: '文档不存在' }, { status: 404 })
    }

    await prisma.document.delete({ where: { id } })

    // 更新文档计数
    await prisma.knowledgeBase.update({
      where: { id: doc.knowledgeBase.id },
      data: { docCount: { decrement: 1 } },
    })

    // 通知 brain-core RAG 删除索引（后台异步）
    void brainCoreFetch(`/api/v1/rag/document/${id}`, { method: 'DELETE' }).catch(() => {})

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('knowledge delete failed:', error)
    return NextResponse.json({ success: false, error: '服务器错误' }, { status: 500 })
  }
}
