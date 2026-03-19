import { NextRequest, NextResponse } from 'next/server';
import { brainCoreFetch } from '@/lib/brain-core-url';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string; execId: string }> },
) {
  try {
    const { id, execId } = await params;
    const resp = await brainCoreFetch(
      `/api/v1/workflows/${id}/executions/${execId}`,
    );
    return NextResponse.json(await resp.json());
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 502 });
  }
}
