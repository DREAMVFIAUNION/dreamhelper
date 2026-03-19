import { NextRequest, NextResponse } from 'next/server'
import { brainCoreFetch } from '@/lib/brain-core-url'

// GET /api/admin/mcp — 代理 brain-core MCP 状态
export async function GET(_req: NextRequest) {
  try {
    const res = await brainCoreFetch('/api/v1/mcp/status', {
      headers: { 'Accept': 'application/json' },
    })
    if (!res.ok) {
      return NextResponse.json({ error: `brain-core ${res.status}` }, { status: 502 })
    }
    const data = await res.json()
    return NextResponse.json(data)
  } catch (e: any) {
    return NextResponse.json(
      { error: 'brain-core 未连接', detail: e.message },
      { status: 502 },
    )
  }
}

// POST /api/admin/mcp — 重连指定服务器
export async function POST(req: NextRequest) {
  try {
    const { server } = await req.json()
    if (!server) {
      return NextResponse.json({ error: '缺少 server 参数' }, { status: 400 })
    }
    const res = await brainCoreFetch(`/api/v1/mcp/servers/${server}/reconnect`, {
      method: 'POST',
      headers: { 'Accept': 'application/json' },
    })
    const data = await res.json()
    return NextResponse.json(data)
  } catch (e: any) {
    return NextResponse.json(
      { error: 'brain-core 未连接', detail: e.message },
      { status: 502 },
    )
  }
}
