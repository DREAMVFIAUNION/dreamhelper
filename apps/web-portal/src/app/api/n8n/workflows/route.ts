import { NextRequest, NextResponse } from 'next/server';

/**
 * [已弃用] n8n 工作流列表 → 重定向到原生工作流 API
 */
import { brainCoreFetch } from '@/lib/brain-core-url';

export async function GET(req: NextRequest) {
  try {
    const status = req.nextUrl.searchParams.get('active_only') === 'true' ? 'active' : '';
    const path = status
      ? `/api/v1/workflows?status=${status}`
      : `/api/v1/workflows`;
    const resp = await brainCoreFetch(path);
    return NextResponse.json(await resp.json());
  } catch (e: any) {
    return NextResponse.json(
      { error: '工作流引擎不可用', detail: e.message },
      { status: 502 },
    );
  }
}
