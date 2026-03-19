import { NextResponse } from 'next/server'
import { brainCoreFetch } from '@/lib/brain-core-url'

export async function GET() {
  try {
    const res = await brainCoreFetch('/api/v1/consciousness/goals')
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ goals: [], error: 'brain-core unreachable' })
  }
}
