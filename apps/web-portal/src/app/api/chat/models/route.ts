import { NextResponse } from 'next/server'
import { brainCoreFetch } from '@/lib/brain-core-url'

export async function GET() {
  try {
    const resp = await brainCoreFetch('/api/v1/chat/models', {
      headers: { 'Content-Type': 'application/json' },
    })
    if (!resp.ok) {
      return NextResponse.json({ models: [] })
    }
    const data = await resp.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ models: [] })
  }
}
