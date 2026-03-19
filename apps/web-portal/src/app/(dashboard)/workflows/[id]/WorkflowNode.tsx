'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import {
  Play, Brain, Bot, Wrench, Globe, Code, GitBranch, Shuffle, Timer, Bell, Clock, Zap, Webhook,
} from 'lucide-react';

const ICON_MAP: Record<string, any> = {
  Play, Brain, Bot, Wrench, Globe, Code, GitBranch, Shuffle, Timer, Bell, Clock, Zap, Webhook,
};

function WorkflowNodeInner({ data, selected }: NodeProps) {
  const d = data as Record<string, any>;
  const Icon = ICON_MAP[d.icon as string] || Zap;
  const color = (d.color as string) || '#FF2D55';
  const inputs = (d.inputs as string[]) || ['input'];
  const outputs = (d.outputs as string[]) || ['output'];

  return (
    <div
      className={`min-w-[140px] bg-card border-2 rounded-lg shadow-card transition-all ${
        selected ? 'border-primary shadow-[0_0_12px_hsl(var(--primary)/0.3)]' : 'border-border hover:border-primary/30'
      }`}
    >
      {/* Input handles */}
      {inputs.map((h, i) => (
        <Handle
          key={`in-${h}`}
          type="target"
          position={Position.Left}
          id={h}
          style={{
            top: `${((i + 1) / (inputs.length + 1)) * 100}%`,
            background: color,
            width: 8, height: 8, border: '2px solid #0D0D12',
          }}
        />
      ))}

      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border/50">
        <div
          className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: color + '20' }}
        >
          <Icon size={12} style={{ color }} />
        </div>
        <div className="min-w-0">
          <div className="text-[11px] font-medium text-foreground truncate">{d.name as string}</div>
          <div className="text-[8px] font-mono text-muted-foreground">{d.type as string}</div>
        </div>
      </div>

      {/* Brief config preview */}
      {d.config && Object.keys(d.config as Record<string, any>).length > 0 && (
        <div className="px-3 py-1.5">
          {Object.entries(d.config as Record<string, any>).slice(0, 2).map(([k, v]) => (
            <div key={k} className="text-[8px] font-mono text-muted-foreground truncate">
              {k}: {String(v).slice(0, 24)}
            </div>
          ))}
        </div>
      )}

      {/* Output handles */}
      {outputs.map((h, i) => (
        <Handle
          key={`out-${h}`}
          type="source"
          position={Position.Right}
          id={h}
          style={{
            top: `${((i + 1) / (outputs.length + 1)) * 100}%`,
            background: color,
            width: 8, height: 8, border: '2px solid #0D0D12',
          }}
        />
      ))}
    </div>
  );
}

export const WorkflowNode = memo(WorkflowNodeInner);
