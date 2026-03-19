'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { Plus, Play, Pause, Trash2, Clock, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface Workflow {
  id: string;
  name: string;
  description: string;
  status: string;
  triggerType: string;
  nodes: any[];
  connections: any[];
  tags: string[];
  runCount: number;
  lastRunAt: string | null;
  lastRunStatus: string | null;
  createdAt: string;
  updatedAt: string;
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-muted-foreground/40',
  active: 'bg-emerald-400',
  paused: 'bg-yellow-500',
  archived: 'bg-muted-foreground/20',
};

const STATUS_LABEL_KEYS: Record<string, string> = {
  draft: 'draft',
  active: 'active',
  paused: 'paused',
  archived: 'archived',
};

const TRIGGER_ICONS: Record<string, string> = {
  manual: '▶',
  cron: '⏰',
  webhook: '🔗',
  event: '⚡',
};

export default function WorkflowsPage() {
  const t = useTranslations('workflows');
  const tc = useTranslations('common');
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  const fetchWorkflows = useCallback(async () => {
    try {
      const url = filter ? `/api/workflows?status=${filter}` : '/api/workflows';
      const res = await fetch(url);
      const data = await res.json();
      setWorkflows(data.data || []);
    } catch {}
    setLoading(false);
  }, [filter]);

  useEffect(() => { fetchWorkflows() }, [fetchWorkflows]);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(t('confirmDelete', { name }))) return;
    await fetch(`/api/workflows/${id}`, { method: 'DELETE' });
    fetchWorkflows();
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-1 h-8 bg-primary rounded-full shadow-[0_0_8px_hsl(var(--primary)/0.4)]" />
          <div>
            <h1 className="font-display text-xl font-bold text-foreground tracking-wider">{t('title')}</h1>
            <p className="text-xs font-mono text-muted-foreground mt-0.5">{t('subtitle')}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1">
            {['', 'draft', 'active', 'paused'].map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={cn(
                  'px-2.5 py-1 text-[10px] font-mono border rounded-md transition-all',
                  filter === s ? 'bg-primary/10 border-primary/40 text-primary' : 'border-border text-muted-foreground hover:text-foreground'
                )}
              >
                {s ? t(STATUS_LABEL_KEYS[s] as any) : t('all')}
              </button>
            ))}
          </div>
          <Button asChild size="sm" className="font-mono gap-1.5">
            <Link href="/workflows/new">
              <Plus size={14} /> {t('create')}
            </Link>
          </Button>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="ml-3 text-muted-foreground font-mono text-sm">{tc('loading')}</span>
        </div>
      )}

      {/* Empty State */}
      {!loading && workflows.length === 0 && (
        <div className="text-center py-20">
          <div className="text-4xl mb-4">⚡</div>
          <h3 className="text-lg font-medium text-foreground mb-2">{t('emptyTitle')}</h3>
          <p className="text-muted-foreground text-sm mb-4">
            {t('emptyDesc')}
          </p>
          <div className="flex items-center justify-center gap-3">
            <Button asChild className="font-mono gap-1.5">
              <Link href="/workflows/new">
                <Plus size={14} /> {t('createFirst')}
              </Link>
            </Button>
            <Button
              variant="outline"
              onClick={async () => {
                await fetch('/api/workflows/seed-examples', { method: 'POST' });
                fetchWorkflows();
              }}
              className="font-mono text-sm gap-1.5"
            >
              <Zap size={14} /> {t('loadExamples')}
            </Button>
          </div>
        </div>
      )}

      {/* Workflow Grid */}
      {!loading && workflows.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workflows.map((wf) => (
            <Card
              key={wf.id}
              className="group hover:border-primary/30 transition-all overflow-hidden"
            >
              <Link href={`/workflows/${wf.id}`} className="block p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-foreground group-hover:text-primary transition-colors truncate">
                    {wf.name}
                  </h3>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs">{TRIGGER_ICONS[wf.triggerType] || '▶'}</span>
                    <span
                      className={`w-2 h-2 rounded-full flex-shrink-0 ${STATUS_COLORS[wf.status] || 'bg-muted-foreground/40'}`}
                      title={STATUS_LABEL_KEYS[wf.status] ? t(STATUS_LABEL_KEYS[wf.status] as any) : wf.status}
                    />
                  </div>
                </div>
                {wf.description && (
                  <p className="text-xs text-muted-foreground mb-2 line-clamp-2">{wf.description}</p>
                )}
                <div className="flex items-center gap-3 text-[10px] text-muted-foreground font-mono">
                  <span>{t('nodes', { n: wf.nodes?.length || 0 })}</span>
                  <span>·</span>
                  <span className="flex items-center gap-0.5">
                    <Play size={8} /> {t('runs', { n: wf.runCount })}
                  </span>
                  {wf.lastRunStatus && (
                    <>
                      <span>·</span>
                      <span className={wf.lastRunStatus === 'success' ? 'text-emerald-400' : 'text-red-400'}>
                        {wf.lastRunStatus === 'success' ? t('success') : t('failed')}
                      </span>
                    </>
                  )}
                </div>
              </Link>
              <div className="flex items-center justify-between px-4 py-2 border-t border-border/50">
                <span className="text-[9px] font-mono text-muted-foreground">
                  {new Date(wf.updatedAt).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })}
                </span>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    variant="ghost"
                    size="icon-xs"
                    onClick={() => handleDelete(wf.id, wf.name)}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 size={12} />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
