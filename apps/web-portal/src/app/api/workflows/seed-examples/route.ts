import { NextResponse } from 'next/server';
import { brainCoreFetch } from '@/lib/brain-core-url';

export async function POST() {
  try {
    const resp = await brainCoreFetch('/api/v1/workflows/seed-examples', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    return NextResponse.json(await resp.json());
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 502 });
  }
}
