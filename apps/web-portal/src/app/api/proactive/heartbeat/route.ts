import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@dreamhelp/auth'
import { brainCoreFetch } from '@/lib/brain-core-url'

export async function POST(req: NextRequest) {
  const token = req.cookies.get('token')?.value
  if (!token) return NextResponse.json({ error: '未登录' }, { status: 401 })
  try { await verifyToken(token) } catch { return NextResponse.json({ error: 'Token 无效' }, { status: 401 }) }

  try {
    const body = await req.json()
    const res = await brainCoreFetch('/api/v1/proactive/heartbeat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    return NextResponse.json(data)
  } catch (e) {
    return NextResponse.json({ status: 'error' })
  }
}
