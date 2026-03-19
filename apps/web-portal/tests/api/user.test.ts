import { describe, it, expect } from 'vitest'
import { NextRequest } from 'next/server'

function mockReq(url: string, init?: RequestInit): NextRequest {
  return new NextRequest(new URL(url, 'http://localhost:3000'), init as any)
}

describe('User API', () => {
  it('GET /api/user/export should reject unauthenticated request', async () => {
    const { GET } = await import('@/app/api/user/export/route')
    const req = mockReq('/api/user/export')
    const res = await GET(req)
    expect(res.status).toBe(401)
    const data = await res.json()
    expect(data.success).toBe(false)
  })

  it('DELETE /api/user/chats should reject unauthenticated request', async () => {
    const { DELETE } = await import('@/app/api/user/chats/route')
    const req = mockReq('/api/user/chats', { method: 'DELETE' })
    const res = await DELETE(req)
    expect(res.status).toBe(401)
    const data = await res.json()
    expect(data.success).toBe(false)
  })
})
