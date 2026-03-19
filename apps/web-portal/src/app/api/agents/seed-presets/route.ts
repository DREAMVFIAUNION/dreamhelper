import { NextResponse } from 'next/server';
import { brainCoreFetch } from '@/lib/brain-core-url';

export async function POST() {
  const resp = await brainCoreFetch('/api/v1/agents/seed-presets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}
