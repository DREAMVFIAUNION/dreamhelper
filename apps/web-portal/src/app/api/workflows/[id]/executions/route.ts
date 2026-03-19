import { NextRequest, NextResponse } from 'next/server';
import { brainCoreFetch } from '@/lib/brain-core-url';

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const limit = req.nextUrl.searchParams.get('limit') || '20';
    const resp = await brainCoreFetch(
      `/api/v1/workflows/${id}/executions?limit=${limit}`,
    );
    return NextResponse.json(await resp.json());
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 502 });
  }
}
