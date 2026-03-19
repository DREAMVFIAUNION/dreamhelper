import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@dreamhelp/auth'
import { brainCoreFetch } from '@/lib/brain-core-url'

export async function GET(req: NextRequest) {
  const token = req.cookies.get('token')?.value
  if (!token) return NextResponse.json({ error: '未登录' }, { status: 401 })

  let userId: string
  try {
    const payload = await verifyToken(token)
    userId = payload.sub
  } catch {
    return NextResponse.json({ error: 'Token 无效' }, { status: 401 })
  }

  try {
    const res = await brainCoreFetch(`/api/v1/proactive/messages/${userId}`)
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ user_id: userId, messages: [] })
  }
}
