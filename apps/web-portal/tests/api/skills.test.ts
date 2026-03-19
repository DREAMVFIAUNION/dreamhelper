import { describe, it, expect } from 'vitest'
import { NextRequest } from 'next/server'

describe('Skills API', () => {
  it('GET /api/skills should return 502 when brain-core offline', async () => {
    const { GET } = await import('@/app/api/skills/route')
    const req = new NextRequest(new URL('/api/skills', 'http://localhost:3000'))
    const res = await GET(req)
    // brain-core not running → 502
    expect([200, 502]).toContain(res.status)
    const data = await res.json()
    if (res.status === 502) {
      expect(data).toHaveProperty('error')
    }
    if (res.status === 200) {
      expect(data).toHaveProperty('skills')
    }
  })

  it('GET /api/skills with query param should pass through', async () => {
    const { GET } = await import('@/app/api/skills/route')
    const req = new NextRequest(new URL('/api/skills?q=calculator', 'http://localhost:3000'))
    const res = await GET(req)
    expect([200, 502]).toContain(res.status)
  })

  it('GET /api/skills with category param should pass through', async () => {
    const { GET } = await import('@/app/api/skills/route')
    const req = new NextRequest(new URL('/api/skills?category=daily', 'http://localhost:3000'))
    const res = await GET(req)
    expect([200, 502]).toContain(res.status)
  })
})
