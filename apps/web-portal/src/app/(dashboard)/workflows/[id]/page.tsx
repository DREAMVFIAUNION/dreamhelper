'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ReactFlow,
  Controls,
  Background,
  addEdge,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type Node,
  type Edge,
  type Connection,
  type NodeTypes,
  Panel,
  type BuiltInNode,
} from '@xyflow/react';

type WfNodeData = Record<string, unknown>;
type WfNode = Node<WfNodeData>;
type WfEdge = Edge;
import '@xyflow/react/dist/style.css';
import {
  Play, Save, ArrowLeft, Trash2, Settings, Plus, ChevronRight,
  Brain, Bot, Wrench, Globe, Code, GitBranch, Shuffle, Timer, Bell, Clock, Zap, Webhook,
} from 'lucide-react';
import { WorkflowNode } from './WorkflowNode';

// ── 类型 ──────────────────────────────────────────────────

interface NodeTypeDesc {
  type: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  color: string;
  inputs: string[];
  outputs: string[];
  configSchema: Record<string, any>;
}

interface WorkflowData {
  id: string;
  name: string;
  description: string;
  status: string;
  triggerType: string;
  triggerConfig: Record<string, any>;
  nodes: any[];
  connections: any[];
  viewport: { x?: number; y?: number; zoom?: number };
  variables: Record<string, any>;
  tags: string[];
}

// ── 图标映射 ──────────────────────────────────────────────

const ICON_MAP: Record<string, any> = {
  Play, Brain, Bot, Wrench, Globe, Code, GitBranch, Shuffle, Timer, Bell, Clock, Zap, Webhook,
};

// ── 自定义节点类型 ────────────────────────────────────────

const nodeTypes: NodeTypes = {
  workflowNode: WorkflowNode,
};

// ── 主组件 ────────────────────────────────────────────────

export default function WorkflowEditorPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;
  const isNew = workflowId === 'new';

  const [workflow, setWorkflow] = useState<WorkflowData | null>(null);
  const [nodeTypeDescs, setNodeTypeDescs] = useState<NodeTypeDesc[]>([]);
  const [categories, setCategories] = useState<Record<string, NodeTypeDesc[]>>({});
  const [nodes, setNodes, onNodesChange] = useNodesState<WfNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<WfEdge>([]);
  const [saving, setSaving] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [showPalette, setShowPalette] = useState(true);
  const [selectedNode, setSelectedNode] = useState<WfNode | null>(null);
  const [wfName, setWfName] = useState('新工作流');
  const [wfDesc, setWfDesc] = useState('');
  const [executionStatus, setExecutionStatus] = useState<any>(null);
  const [dynamicAgents, setDynamicAgents] = useState<string[]>([]);

  // 加载节点类型
  useEffect(() => {
    fetch('/api/workflows/node-types')
      .then(r => r.json())
      .then(data => {
        setNodeTypeDescs(data.types || []);
        setCategories(data.categories || {});
      })
      .catch(() => {});
    // 加载动态 Agent 列表（供 agent 节点选择器使用）
    fetch('/api/agents')
      .then(r => r.json())
      .then(data => {
        const names = (data.data || [])
          .filter((a: any) => a.status === 'active')
          .map((a: any) => (a.name as string).toLowerCase().replace(/\s+/g, '_').replace(/-/g, '_'));
        setDynamicAgents(names);
      })
      .catch(() => {});
  }, []);

  // 加载工作流数据
  useEffect(() => {
    if (isNew) return;
    fetch(`/api/workflows/${workflowId}`)
      .then(r => r.json())
      .then((wf: WorkflowData) => {
        setWorkflow(wf);
        setWfName(wf.name);
        setWfDesc(wf.description || '');
        // 转换为 React Flow 格式
        const rfNodes: WfNode[] = (wf.nodes || []).map((n: any) => ({
          id: n.id as string,
          type: 'workflowNode' as const,
          position: n.position || { x: 0, y: 0 },
          data: { ...n } as WfNodeData,
        }));
        const rfEdges: WfEdge[] = (wf.connections || []).map((c: any) => ({
          id: c.id as string,
          source: c.source as string,
          target: c.target as string,
          sourceHandle: c.sourceHandle || 'output',
          targetHandle: c.targetHandle || 'input',
          animated: true,
          style: { stroke: '#FF2D55', strokeWidth: 2 },
        }));
        setNodes(rfNodes);
        setEdges(rfEdges);
      })
      .catch(() => {});
  }, [workflowId, isNew]);

  const onConnect = useCallback((connection: Connection) => {
    setEdges(eds => addEdge({
      ...connection,
      animated: true,
      style: { stroke: '#FF2D55', strokeWidth: 2 },
    }, eds));
  }, [setEdges]);

  // 添加节点
  const addNode = (nodeType: NodeTypeDesc) => {
    const id = `node_${Date.now()}`;
    const newNode: WfNode = {
      id,
      type: 'workflowNode' as const,
      position: { x: 250 + Math.random() * 200, y: 100 + Math.random() * 200 },
      data: {
        id,
        type: nodeType.type,
        name: nodeType.name,
        config: {},
        icon: nodeType.icon,
        color: nodeType.color,
        category: nodeType.category,
        inputs: nodeType.inputs,
        outputs: nodeType.outputs,
        configSchema: nodeType.configSchema,
      } as WfNodeData,
    };
    setNodes(nds => [...nds, newNode]);
  };

  // 保存
  const handleSave = async () => {
    setSaving(true);
    const wfNodes = nodes.map(n => ({
      id: n.id,
      type: n.data.type,
      name: n.data.name,
      config: n.data.config || {},
      position: n.position,
    }));
    const wfConnections = edges.map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
      sourceHandle: e.sourceHandle || 'output',
      targetHandle: e.targetHandle || 'input',
    }));

    try {
      if (isNew) {
        const res = await fetch('/api/workflows', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: wfName, description: wfDesc,
            nodes: wfNodes, connections: wfConnections,
          }),
        });
        const created = await res.json();
        router.push(`/workflows/${created.id}`);
      } else {
        await fetch(`/api/workflows/${workflowId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: wfName, description: wfDesc,
            nodes: wfNodes, connections: wfConnections,
          }),
        });
      }
    } catch {}
    setSaving(false);
  };

  // 执行
  const handleExecute = async () => {
    if (isNew) return;
    setExecuting(true);
    setExecutionStatus(null);
    try {
      const res = await fetch(`/api/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trigger_data: {} }),
      });
      const data = await res.json();
      setExecutionStatus({ executionId: data.executionId, status: 'running' });

      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const execRes = await fetch(`/api/workflows/${workflowId}/executions`);
          const execData = await execRes.json();
          const latest = (execData.data || []).find((e: any) => e.id === data.executionId);
          if (latest) {
            setExecutionStatus(latest);
            if (latest.status !== 'pending' && latest.status !== 'running') {
              clearInterval(pollInterval);
              setExecuting(false);
            }
          }
        } catch { clearInterval(pollInterval); setExecuting(false); }
      }, 1000);

      setTimeout(() => { clearInterval(pollInterval); setExecuting(false); }, 60000);
    } catch { setExecuting(false); }
  };

  const onNodeClick = useCallback((_: any, node: WfNode) => {
    setSelectedNode(node);
  }, []);

  // Helper: 更新节点 data（安全合并 Record<string, unknown>）
  const updateNodeData = (nodeId: string, patch: Record<string, unknown>) => {
    setNodes(nds => nds.map(n => {
      if (n.id !== nodeId) return n;
      const newData: WfNodeData = {};
      for (const k of Object.keys(n.data)) newData[k] = n.data[k];
      for (const k of Object.keys(patch)) newData[k] = patch[k];
      return { ...n, data: newData };
    }));
  };

  const updateNodeConfig = (nodeId: string, configKey: string, value: unknown) => {
    setNodes(nds => nds.map(n => {
      if (n.id !== nodeId) return n;
      const oldConfig = (n.data.config as Record<string, unknown>) || {};
      const newConfig: Record<string, unknown> = { ...oldConfig, [configKey]: value };
      const newData: WfNodeData = {};
      for (const k of Object.keys(n.data)) newData[k] = n.data[k];
      newData.config = newConfig;
      return { ...n, data: newData };
    }));
    // Sync selectedNode
    setSelectedNode(prev => {
      if (!prev || prev.id !== nodeId) return prev;
      const oldConfig = (prev.data.config as Record<string, unknown>) || {};
      const newConfig: Record<string, unknown> = { ...oldConfig, [configKey]: value };
      const newData: WfNodeData = {};
      for (const k of Object.keys(prev.data)) newData[k] = prev.data[k];
      newData.config = newConfig;
      return { ...prev, data: newData };
    });
  };

  const d = (key: string): any => selectedNode?.data?.[key];

  const CATEGORY_LABELS: Record<string, string> = {
    trigger: '触发器', ai: 'AI 智能', skill: '技能工具', logic: '逻辑控制', output: '输出',
  };

  const CATEGORY_ORDER = ['trigger', 'ai', 'skill', 'logic', 'output'];

  return (
    <div className="h-[calc(100vh-48px)] flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-card border-b border-border flex-shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push('/workflows')} className="text-muted-foreground hover:text-primary transition-colors">
            <ArrowLeft size={16} />
          </button>
          <input
            value={wfName}
            onChange={e => setWfName(e.target.value)}
            className="bg-transparent text-foreground font-medium text-sm border-b border-transparent hover:border-border focus:border-primary outline-none px-1 py-0.5 w-48"
          />
          <span className="text-[9px] font-mono text-muted-foreground">
            {isNew ? '新建' : workflowId.slice(0, 8)}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {executionStatus && (
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
              executionStatus.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' :
              executionStatus.status === 'failed' ? 'bg-red-500/10 text-red-400' :
              'bg-yellow-500/10 text-yellow-500'
            }`}>
              {executionStatus.status === 'running' ? '执行中...' :
               executionStatus.status === 'success' ? `成功 · ${executionStatus.completedNodes}节点 · ${executionStatus.totalLatencyMs}ms` :
               executionStatus.status === 'failed' ? '执行失败' : executionStatus.status}
            </span>
          )}
          {!isNew && (
            <Link
              href={`/workflows/${workflowId}/executions`}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-mono border border-border text-muted-foreground hover:text-primary hover:border-primary/40 transition-all rounded-md"
            >
              <Clock size={12} /> 历史
            </Link>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-mono border border-border text-muted-foreground hover:text-primary hover:border-primary/40 transition-all rounded-md disabled:opacity-50"
          >
            <Save size={12} /> {saving ? '保存中...' : '保存'}
          </button>
          {!isNew && (
            <button
              onClick={handleExecute}
              disabled={executing}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-mono bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              <Play size={12} /> {executing ? '执行中...' : '运行'}
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Node Palette */}
        {showPalette && (
          <div className="w-56 bg-card border-r border-border overflow-y-auto scrollbar-none flex-shrink-0">
            <div className="p-2">
              <div className="text-[9px] font-mono text-muted-foreground uppercase tracking-wider px-2 py-1">节点面板</div>
              {CATEGORY_ORDER.map(cat => {
                const catNodes = categories[cat] || [];
                if (catNodes.length === 0) return null;
                return (
                  <div key={cat} className="mb-2">
                    <div className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-wider px-2 py-1">
                      {CATEGORY_LABELS[cat] || cat}
                    </div>
                    {catNodes.map(nt => {
                      const Icon = ICON_MAP[nt.icon] || Zap;
                      return (
                        <button
                          key={nt.type}
                          onClick={() => addNode(nt)}
                          className="w-full flex items-center gap-2 px-2 py-1.5 rounded text-left text-xs hover:bg-accent transition-colors group"
                        >
                          <div className="w-5 h-5 rounded flex items-center justify-center flex-shrink-0" style={{ backgroundColor: nt.color + '20' }}>
                            <Icon size={10} style={{ color: nt.color }} />
                          </div>
                          <div className="min-w-0">
                            <div className="text-foreground text-[11px] truncate group-hover:text-primary transition-colors">{nt.name}</div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* React Flow Canvas */}
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            className="bg-background"
            defaultEdgeOptions={{ animated: true, style: { stroke: '#FF2D55', strokeWidth: 2 } }}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#ffffff08" />
            <Controls className="!bg-card !border-border !rounded !shadow-card" />
            <Panel position="top-left">
              <button
                onClick={() => setShowPalette(!showPalette)}
                className="px-2 py-1 bg-card border border-border rounded text-[10px] font-mono text-muted-foreground hover:text-primary transition-colors"
              >
                {showPalette ? '◀ 收起' : '▶ 节点'}
              </button>
            </Panel>
          </ReactFlow>
        </div>

        {/* Config Panel (right side) */}
        {selectedNode && (
          <div className="w-64 bg-card border-l border-border overflow-y-auto scrollbar-none flex-shrink-0">
            <div className="p-3 border-b border-border">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-foreground">{String(d('name') || '')}</span>
                <button onClick={() => setSelectedNode(null)} className="text-muted-foreground hover:text-primary text-xs">✕</button>
              </div>
              <span className="text-[9px] font-mono text-muted-foreground">{String(d('type') || '')}</span>
            </div>
            <div className="p-3 space-y-3">
              {/* 节点名称 */}
              <div>
                <label className="text-[9px] font-mono text-muted-foreground block mb-1">名称</label>
                <input
                  value={String(d('name') || '')}
                  onChange={e => {
                    updateNodeData(selectedNode.id, { name: e.target.value });
                    setSelectedNode(prev => {
                      if (!prev) return null;
                      const nd: WfNodeData = {};
                      for (const k of Object.keys(prev.data)) nd[k] = prev.data[k];
                      nd.name = e.target.value;
                      return { ...prev, data: nd };
                    });
                  }}
                  className="w-full bg-secondary border border-border rounded px-2 py-1 text-xs text-foreground outline-none focus:border-primary/40"
                />
              </div>
              {/* 配置字段 */}
              {d('configSchema') && Object.entries(d('configSchema') as Record<string, any>).map(([key, schema]: [string, any]) => {
                const cfgVal = (d('config') as any)?.[key] ?? schema.default ?? '';
                return (
                  <div key={key}>
                    <label className="text-[9px] font-mono text-muted-foreground block mb-1">{schema.label || key}</label>
                    {schema.type === 'select' ? (
                      <select
                        value={String(cfgVal)}
                        onChange={e => updateNodeConfig(selectedNode.id, key, e.target.value)}
                        className="w-full bg-secondary border border-border rounded px-2 py-1 text-xs text-foreground outline-none focus:border-primary/40"
                      >
                        {(schema.options || []).map((opt: string) => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                        {/* Agent 节点: 追加 DB 中的动态 Agent */}
                        {key === 'agent' && d('type') === 'agent' && dynamicAgents
                          .filter(a => !(schema.options || []).includes(a))
                          .map((a: string) => (
                            <option key={`db_${a}`} value={a}>{a} (自定义)</option>
                          ))
                        }
                      </select>
                    ) : schema.type === 'textarea' || schema.type === 'code' ? (
                      <textarea
                        value={String(cfgVal)}
                        onChange={e => updateNodeConfig(selectedNode.id, key, e.target.value)}
                        rows={schema.type === 'code' ? 6 : 3}
                        className="w-full bg-secondary border border-border rounded px-2 py-1 text-xs text-foreground outline-none focus:border-primary/40 font-mono resize-none"
                        placeholder={schema.placeholder}
                      />
                    ) : schema.type === 'boolean' ? (
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={Boolean(cfgVal)}
                          onChange={e => updateNodeConfig(selectedNode.id, key, e.target.checked)}
                          className="accent-primary"
                        />
                        <span className="text-xs text-muted-foreground">{schema.label}</span>
                      </label>
                    ) : (
                      <input
                        type={schema.type === 'number' ? 'number' : 'text'}
                        value={String(cfgVal)}
                        onChange={e => updateNodeConfig(selectedNode.id, key, schema.type === 'number' ? Number(e.target.value) : e.target.value)}
                        placeholder={schema.placeholder}
                        className="w-full bg-secondary border border-border rounded px-2 py-1 text-xs text-foreground outline-none focus:border-primary/40"
                      />
                    )}
                  </div>
                );
              })}
              {/* 删除节点 */}
              <button
                onClick={() => {
                  setNodes(nds => nds.filter(n => n.id !== selectedNode.id));
                  setEdges(eds => eds.filter(e => e.source !== selectedNode.id && e.target !== selectedNode.id));
                  setSelectedNode(null);
                }}
                className="w-full flex items-center justify-center gap-1 px-2 py-1.5 text-xs text-red-400 border border-red-400/30 rounded hover:bg-red-400/10 transition-colors"
              >
                <Trash2 size={10} /> 删除节点
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
