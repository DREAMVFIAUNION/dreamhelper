import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@dreamhelp/auth';
import { brainCoreFetch } from '@/lib/brain-core-url';

async function requireAuth(req: NextRequest): Promise<string | NextResponse> {
  const token = req.cookies.get('token')?.value
  if (!token) return NextResponse.json({ error: '未登录' }, { status: 401 })
  try {
    const payload = await verifyToken(token)
    return payload.sub
  } catch {
    return NextResponse.json({ error: 'Token 无效' }, { status: 401 })
  }
}

export async function GET(req: NextRequest) {
  const auth = await requireAuth(req)
  if (auth instanceof NextResponse) return auth

  const { searchParams } = new URL(req.url);
  const qs = searchParams.toString();
  const resp = await brainCoreFetch(`/api/v1/agents${qs ? `?${qs}` : ''}`, {
    headers: { 'Content-Type': 'application/json' },
  });
  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}

export async function POST(req: NextRequest) {
  const auth = await requireAuth(req)
  if (auth instanceof NextResponse) return auth

  const body = await req.json();
  const resp = await brainCoreFetch('/api/v1/agents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}
