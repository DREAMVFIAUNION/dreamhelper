'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, CheckCircle, XCircle, Clock, Loader2, ChevronDown, ChevronRight } from 'lucide-react';

interface Step {
  id: string;
  nodeId: string;
  nodeName: string;
  nodeType: string;
  status: string;
  inputData: any;
  outputData: any;
  error: string | null;
  tokens: number;
  latencyMs: number;
}

interface ExecutionDetail {
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
  steps: Step[];
}

const STATUS_ICON: Record<string, { icon: any; color: string }> = {
  pending: { icon: Clock, color: 'text-yellow-500' },
  running: { icon: Loader2, color: 'text-blue-400' },
  success: { icon: CheckCircle, color: 'text-emerald-400' },
  failed: { icon: XCircle, color: 'text-red-400' },
  skipped: { icon: Clock, color: 'text-muted-foreground/40' },
};

export default function ExecutionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;
  const execId = params.execId as string;

  const [execution, setExecution] = useState<ExecutionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const res = await fetch(`/api/workflows/${workflowId}/executions/${execId}`);
        const data = await res.json();
        setExecution(data);
      } catch {}
      setLoading(false);
    };
    fetchDetail();

    // Auto-refresh while running
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/workflows/${workflowId}/executions/${execId}`);
        const data = await res.json();
        setExecution(data);
        if (data.status !== 'pending' && data.status !== 'running') {
          clearInterval(interval);
        }
      } catch {}
    }, 2000);

    return () => clearInterval(interval);
  }, [workflowId, execId]);

  const toggleStep = (stepId: string) => {
    setExpandedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepId)) next.delete(stepId); else next.add(stepId);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        <span className="ml-3 text-muted-foreground font-mono text-sm">加载中...</span>
      </div>
    );
  }

  if (!execution) {
    return <div className="p-6 text-muted-foreground">执行记录不存在</div>;
  }

  const statusCfg = STATUS_ICON[execution.status] ?? STATUS_ICON['pending']!;
  const StatusIcon = statusCfg.icon;
  const duration = execution.finishedAt
    ? ((new Date(execution.finishedAt).getTime() - new Date(execution.startedAt).getTime()) / 1000).toFixed(1)
    : null;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push(`/workflows/${workflowId}/executions`)} className="text-muted-foreground hover:text-primary transition-colors">
          <ArrowLeft size={16} />
        </button>
        <div className="w-1 h-8 bg-primary rounded-full shadow-[0_0_8px_hsl(var(--primary)/0.4)]" />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <StatusIcon size={18} className={`${statusCfg.color} ${execution.status === 'running' ? 'animate-spin' : ''}`} />
            <h1 className="font-display text-xl font-bold text-foreground tracking-wider">
              执行详情
            </h1>
            <span className={`text-xs font-mono font-bold ${statusCfg.color}`}>
              {execution.status === 'success' ? '成功' : execution.status === 'failed' ? '失败' : execution.status === 'running' ? '执行中' : execution.status}
            </span>
          </div>
          <p className="text-xs font-mono text-muted-foreground mt-0.5">{execId.slice(0, 12)}</p>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        {[
          { label: '节点', value: `${execution.completedNodes}/${execution.totalNodes}` },
          { label: '耗时', value: duration ? `${duration}s` : '...' },
          { label: 'Token', value: execution.totalTokens.toString() },
          { label: '延迟', value: `${execution.totalLatencyMs}ms` },
        ].map(s => (
          <div key={s.label} className="bg-card border border-border rounded-md p-3">
            <div className="text-[9px] font-mono text-muted-foreground uppercase">{s.label}</div>
            <div className="text-lg font-bold font-mono text-foreground">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Error */}
      {execution.error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400 font-mono">
          {execution.error}
        </div>
      )}

      {/* Steps Timeline */}
      <div className="space-y-1">
        <div className="text-[9px] font-mono text-muted-foreground uppercase tracking-wider mb-2">节点执行步骤</div>
        {(execution.steps || []).map((step, i) => {
          const sCfg = STATUS_ICON[step.status] ?? STATUS_ICON['pending']!;
          const SIcon = sCfg.icon;
          const expanded = expandedSteps.has(step.id);

          return (
            <div key={step.id} className="border border-border rounded-md bg-card">
              <button
                onClick={() => toggleStep(step.id)}
                className="w-full flex items-center gap-3 p-3 hover:bg-accent transition-colors text-left"
              >
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-[9px] font-mono text-muted-foreground w-4 text-right">{i + 1}</span>
                  <SIcon size={14} className={`${sCfg.color} ${step.status === 'running' ? 'animate-spin' : ''}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-medium text-foreground">{step.nodeName}</span>
                  <span className="text-[9px] font-mono text-muted-foreground ml-2">{step.nodeType}</span>
                </div>
                <div className="flex items-center gap-3 text-[9px] font-mono text-muted-foreground flex-shrink-0">
                  {step.tokens > 0 && <span>{step.tokens}t</span>}
                  {step.latencyMs > 0 && <span>{step.latencyMs}ms</span>}
                  {expanded ? <ChevronDown size={10} /> : <ChevronRight size={10} />}
                </div>
              </button>

              {expanded && (
                <div className="px-3 pb-3 space-y-2 border-t border-border/50">
                  {step.error && (
                    <div className="mt-2 p-2 bg-red-500/10 rounded text-[10px] font-mono text-red-400">
                      {step.error}
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    <div>
                      <div className="text-[8px] font-mono text-muted-foreground uppercase mb-1">输入</div>
                      <pre className="text-[9px] font-mono text-secondary-foreground bg-secondary rounded-md p-2 max-h-32 overflow-auto scrollbar-none">
                        {JSON.stringify(step.inputData, null, 2)}
                      </pre>
                    </div>
                    <div>
                      <div className="text-[8px] font-mono text-muted-foreground uppercase mb-1">输出</div>
                      <pre className="text-[9px] font-mono text-secondary-foreground bg-secondary rounded-md p-2 max-h-32 overflow-auto scrollbar-none">
                        {JSON.stringify(step.outputData, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
