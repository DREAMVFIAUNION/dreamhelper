'use client'

const AGENTS = [
  { id: 'react_agent', name: 'ReAct Agent', desc: '工具调用专家，支持搜索/计算/日期等工具', temp: 0.7, icon: '🔧', color: 'brand', keywords: '搜索, 查询, 帮我算, 工具' },
  { id: 'code_agent', name: 'Code Agent', desc: '编程专家，擅长代码生成/调试/重构', temp: 0.5, icon: '💻', color: 'cyber-blue', keywords: '代码, 编程, Python, 函数, 装饰器' },
  { id: 'writing_agent', name: 'Writing Agent', desc: '写作专家，文案/翻译/总结/改写', temp: 0.8, icon: '✍️', color: 'cyber-purple', keywords: '翻译, 写作, 文案, 总结, 润色' },
  { id: 'analysis_agent', name: 'Analysis Agent', desc: '分析专家，深度分析/对比/评估', temp: 0.4, icon: '📊', color: 'cyber-green', keywords: '分析, 对比, 优劣, 评估, 方案' },
]

export default function AdminAgentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-mono font-bold text-foreground">智能体管理</h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">{AGENTS.length} 个内置智能体</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {AGENTS.map((a) => (
          <div key={a.id} className="bg-card border border-border p-4 rounded-md">
            <div className="flex items-start gap-3">
              <div className="text-2xl">{a.icon}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-foreground">{a.name}</span>
                  <span className={`text-[8px] font-mono px-1.5 py-0.5 border border-${a.color}/30 text-${a.color}`}>ACTIVE</span>
                </div>
                <p className="text-[10px] font-mono text-muted-foreground mt-1">{a.desc}</p>
                <div className="mt-2 space-y-1">
                  <div className="flex items-center gap-2 text-[9px] font-mono text-muted-foreground/60">
                    <span>Temperature:</span>
                    <div className="flex-1 h-1 bg-secondary rounded overflow-hidden">
                      <div className="h-full bg-primary/50 rounded" style={{ width: `${a.temp * 100}%` }} />
                    </div>
                    <span>{a.temp}</span>
                  </div>
                  <div className="text-[9px] font-mono text-muted-foreground/60">
                    路由关键词: <span className="text-muted-foreground/80">{a.keywords}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-card border border-border p-4 rounded-md">
        <h2 className="text-sm font-mono font-bold text-foreground mb-2">路由策略</h2>
        <div className="text-[10px] font-mono text-muted-foreground space-y-1">
          <p>1. 关键词快速匹配 — 匹配 ≥1 个关键词即路由到对应 Agent</p>
          <p>2. LLM 智能路由 — 无关键词命中时使用 LLM 分类</p>
          <p>3. 默认回退 — 无法判定时使用普通对话模式</p>
        </div>
      </div>
    </div>
  )
}
