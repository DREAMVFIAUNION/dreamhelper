/**
 * Next.js API 代理 — Skills API
 * GET /api/skills → brain-core /api/v1/skills/list
 * POST /api/skills → brain-core /api/v1/skills/execute
 */

import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@dreamhelp/auth'
import { brainCoreFetch } from '@/lib/brain-core-url'

async function requireAuth(req: NextRequest): Promise<string | NextResponse> {
  const token = req.cookies.get('token')?.value
  if (!token) return NextResponse.json({ error: '未登录' }, { status: 401 })
  try {
    const payload = await verifyToken(token)
    return payload.sub
  } catch {
    return NextResponse.json({ error: 'Token 无效' }, { status: 401 })
  }
}

export async function GET(req: NextRequest) {
  const auth = await requireAuth(req)
  if (auth instanceof NextResponse) return auth
  const { searchParams } = new URL(req.url)
  const q = searchParams.get('q')
  const category = searchParams.get('category')

  let endpoint = '/api/v1/skills/list'
  if (q) {
    endpoint = `/api/v1/skills/search?q=${encodeURIComponent(q)}`
  } else if (category) {
    endpoint = `/api/v1/skills/category/${encodeURIComponent(category)}`
  }

  try {
    const resp = await brainCoreFetch(endpoint)
    if (!resp.ok) {
      return NextResponse.json({ error: 'Brain-core error' }, { status: resp.status })
    }
    const data = await resp.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: 'Brain-core 连接失败' }, { status: 502 })
  }
}

export async function POST(req: NextRequest) {
  const auth = await requireAuth(req)
  if (auth instanceof NextResponse) return auth

  try {
    const body = await req.json()

    const resp = await brainCoreFetch('/api/v1/skills/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!resp.ok) {
      return NextResponse.json({ error: 'Brain-core error' }, { status: resp.status })
    }

    const data = await resp.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: 'Brain-core 连接失败' }, { status: 502 })
  }
}
