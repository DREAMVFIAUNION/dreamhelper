import { NextRequest, NextResponse } from 'next/server'
import { brainCoreFetch } from '@/lib/brain-core-url'

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData()
    const res = await brainCoreFetch('/api/v1/multimodal/stt', {
      method: 'POST',
      body: formData,
    })
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ text: '', error: 'STT service unavailable' }, { status: 500 })
  }
}
