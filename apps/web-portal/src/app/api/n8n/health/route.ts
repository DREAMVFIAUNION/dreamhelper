import { NextResponse } from 'next/server';

/**
 * [已弃用] n8n 外部服务已替换为原生工作流引擎
 * 保留端点以兼容旧客户端，返回引擎健康状态
 */
import { brainCoreFetch } from '@/lib/brain-core-url';

export async function GET() {
  try {
    const resp = await brainCoreFetch('/health');
    const data = await resp.json();
    return NextResponse.json({
      service: 'workflow-engine',
      healthy: data.status === 'ok',
      note: 'n8n 已替换为原生工作流引擎，请使用 /api/workflows',
    });
  } catch (e: any) {
    return NextResponse.json(
      { service: 'workflow-engine', healthy: false, error: e.message },
      { status: 502 },
    );
  }
}
