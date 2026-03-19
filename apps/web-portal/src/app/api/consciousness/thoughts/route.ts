import { NextRequest, NextResponse } from 'next/server'
import { brainCoreFetch } from '@/lib/brain-core-url'

export async function GET(req: NextRequest) {
  try {
    const limit = req.nextUrl.searchParams.get('limit') || '10'
    const res = await brainCoreFetch(`/api/v1/consciousness/thoughts?limit=${limit}`)
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ thoughts: [], stats: {} })
  }
}
