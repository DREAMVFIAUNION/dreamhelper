import { NextResponse } from 'next/server'
import { brainCoreFetch } from '@/lib/brain-core-url'

export async function GET() {
  try {
    const res = await brainCoreFetch('/api/v1/consciousness/status')
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ enabled: false, started: false, error: 'brain-core unreachable' })
  }
}
