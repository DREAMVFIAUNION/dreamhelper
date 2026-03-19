import { NextRequest, NextResponse } from 'next/server';
import { brainCoreFetch } from '@/lib/brain-core-url';

export async function GET(req: NextRequest) {
  try {
    const status = req.nextUrl.searchParams.get('status') || '';
    const path = status
      ? `/api/v1/workflows?status=${status}`
      : `/api/v1/workflows`;
    const resp = await brainCoreFetch(path);
    return NextResponse.json(await resp.json());
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 502 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const resp = await brainCoreFetch('/api/v1/workflows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return NextResponse.json(await resp.json());
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 502 });
  }
}
