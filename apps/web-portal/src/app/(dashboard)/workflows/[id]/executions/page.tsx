'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, CheckCircle, XCircle, Clock, Loader2, Play } from 'lucide-react';

interface Execution {
  id: string;
  workflowId: string;
  status: string;
  triggerType: string;
  totalNodes: number;
  completedNodes: number;
  totalTokens: number;
  totalLatencyMs: number;
  error: string | null;
  startedAt: string;
  finishedAt: string | null;
}

const STATUS_CONFIG: Record<string, { icon: any; color: string; label: string }> = {
  pending: { icon: Clock, color: 'text-yellow-500', label: '等待中' },
  running: { icon: Loader2, color: 'text-blue-400', label: '执行中' },
  success: { icon: CheckCircle, color: 'text-emerald-400', label: '成功' },
  failed: { icon: XCircle, color: 'text-red-400', label: '失败' },
  cancelled: { icon: XCircle, color: 'text-muted-foreground', label: '已取消' },
};

export default function ExecutionsPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchExecutions = useCallback(async () => {
    try {
      const res = await fetch(`/api/workflows/${workflowId}/executions?limit=50`);
      const data = await res.json();
      setExecutions(data.data || []);
    } catch {}
    setLoading(false);
  }, [workflowId]);

  useEffect(() => { fetchExecutions(); }, [fetchExecutions]);

  // Auto-refresh if any execution is running
  useEffect(() => {
    const hasRunning = executions.some(e => e.status === 'running' || e.status === 'pending');
    if (!hasRunning) return;
    const interval = setInterval(fetchExecutions, 2000);
    return () => clearInterval(interval);
  }, [executions, fetchExecutions]);

  const handleExecute = async () => {
    await fetch(`/api/workflows/${workflowId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger_data: {} }),
    });
    fetchExecutions();
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push(`/workflows/${workflowId}`)} className="text-muted-foreground hover:text-primary transition-colors">
            <ArrowLeft size={16} />
          </button>
          <div className="w-1 h-8 bg-primary rounded-full shadow-[0_0_8px_hsl(var(--primary)/0.4)]" />
          <div>
            <h1 className="font-display text-xl font-bold text-foreground tracking-wider">执行历史</h1>
            <p className="text-xs font-mono text-muted-foreground mt-0.5">EXECUTIONS · {workflowId.slice(0, 8)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExecute}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-mono bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            <Play size={12} /> 手动执行
          </button>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="ml-3 text-muted-foreground font-mono text-sm">加载中...</span>
        </div>
      )}

      {/* Empty */}
      {!loading && executions.length === 0 && (
        <div className="text-center py-20">
          <Clock size={32} className="mx-auto text-muted-foreground mb-3" />
          <h3 className="text-lg font-medium text-foreground mb-2">暂无执行记录</h3>
          <p className="text-muted-foreground text-sm">返回编辑器执行工作流，或点击上方「手动执行」</p>
        </div>
      )}

      {/* Execution List */}
      {!loading && executions.length > 0 && (
        <div className="space-y-2">
          {executions.map((exec) => {
            const cfg = STATUS_CONFIG[exec.status] ?? STATUS_CONFIG['pending']!;
            const Icon = cfg.icon;
            const duration = exec.finishedAt
              ? Math.round((new Date(exec.finishedAt).getTime() - new Date(exec.startedAt).getTime()) / 1000)
              : null;

            return (
              <Link
                key={exec.id}
                href={`/workflows/${workflowId}/executions/${exec.id}`}
                className="flex items-center gap-4 p-4 bg-card border border-border hover:border-primary/40 rounded-md transition-all group"
              >
                <Icon
                  size={18}
                  className={`${cfg.color} flex-shrink-0 ${exec.status === 'running' ? 'animate-spin' : ''}`}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-mono font-bold ${cfg.color}`}>{cfg.label}</span>
                    <span className="text-[9px] font-mono text-muted-foreground">{exec.id.slice(0, 8)}</span>
                  </div>
                  {exec.error && (
                    <p className="text-[10px] text-red-400 font-mono mt-0.5 truncate">{exec.error}</p>
                  )}
                </div>
                <div className="flex items-center gap-4 text-[10px] font-mono text-muted-foreground flex-shrink-0">
                  <span>{exec.completedNodes}/{exec.totalNodes} 节点</span>
                  {exec.totalTokens > 0 && <span>{exec.totalTokens} tokens</span>}
                  {duration !== null && <span>{duration}s</span>}
                  {exec.totalLatencyMs > 0 && <span>{exec.totalLatencyMs}ms</span>}
                  <span>{new Date(exec.startedAt).toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
