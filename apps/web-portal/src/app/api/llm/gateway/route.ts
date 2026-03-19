import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from '@dreamhelp/auth';
import { brainCoreFetch } from '@/lib/brain-core-url';

export async function GET(req: NextRequest) {
  const token = req.cookies.get('token')?.value
  if (!token) return NextResponse.json({ error: '未登录' }, { status: 401 })
  try { await verifyToken(token) } catch { return NextResponse.json({ error: 'Token 无效' }, { status: 401 }) }

  try {
    const resp = await brainCoreFetch('/api/v1/llm/gateway/stats');
    const data = await resp.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { error: "Failed to fetch gateway stats" },
      { status: 502 }
    );
  }
}
