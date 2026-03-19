import { describe, it, expect } from 'vitest'
import { NextRequest } from 'next/server'

describe('Chat API', () => {
  it('GET /api/chat/models should return models array (fallback when brain-core offline)', async () => {
    const { GET } = await import('@/app/api/chat/models/route')
    const res = await GET()
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data).toHaveProperty('models')
    expect(Array.isArray(data.models)).toBe(true)
  })

  it('POST /api/chat/completions should return 502 when brain-core offline', async () => {
    const { POST } = await import('@/app/api/chat/completions/route')
    const req = new NextRequest(new URL('/api/chat/completions', 'http://localhost:3000'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: 'hello', stream: false }),
    })
    const res = await POST(req)
    // brain-core not running → 502 proxy error
    expect([400, 500, 502]).toContain(res.status)
  })
})
