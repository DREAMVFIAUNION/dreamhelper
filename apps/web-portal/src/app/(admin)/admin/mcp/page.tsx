'use client'

import { useState, useEffect, useCallback } from 'react'
import { CheckCircle, AlertCircle, RefreshCw, Plug, Wrench, Server, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MCPServer {
  name: string
  description: string
  transport: string
  connected: boolean
  tools_count: number
  tools: string[]
  error: string
}

interface MCPStatus {
  total_servers: number
  connected_servers: number
  total_tools: number
  servers: MCPServer[]
}

export default function AdminMCPPage() {
  const [status, setStatus] = useState<MCPStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reconnecting, setReconnecting] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      const res = await fetch('/api/admin/mcp')
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.error || `HTTP ${res.status}`)
      }
      const data: MCPStatus = await res.json()
      setStatus(data)
    } catch (e: any) {
      setError(e.message || '获取 MCP 状态失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchStatus() }, [fetchStatus])

  const handleReconnect = async (serverName: string) => {
    setReconnecting(serverName)
    try {
      await fetch('/api/admin/mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server: serverName }),
      })
      await fetchStatus()
    } catch {
      // ignore
    } finally {
      setReconnecting(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-mono font-bold text-foreground">MCP 服务管理</h1>
          <p className="text-xs font-mono text-muted-foreground mt-1">
            Model Context Protocol 外接工具服务状态
          </p>
        </div>
        <button
          onClick={fetchStatus}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-mono bg-secondary border border-border rounded-md hover:bg-secondary/80 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={12} className={cn(loading && 'animate-spin')} />
          刷新
        </button>
      </div>

      {/* 总览卡片 */}
      {status && (
        <div className="grid grid-cols-3 gap-3">
          <StatCard label="服务器总数" value={status.total_servers} icon={<Server size={14} />} />
          <StatCard
            label="已连接"
            value={status.connected_servers}
            icon={<Plug size={14} />}
            highlight={status.connected_servers === status.total_servers ? 'green' : 'yellow'}
          />
          <StatCard label="可用工具" value={status.total_tools} icon={<Wrench size={14} />} />
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-mono px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {/* 服务器列表 */}
      {status && (
        <div className="bg-card border border-border p-4 rounded-md">
          <h2 className="text-sm font-mono font-bold text-foreground mb-3">MCP 服务器</h2>
          <div className="space-y-2">
            {status.servers.map((s) => (
              <div
                key={s.name}
                className="bg-secondary border border-border/50 rounded-md p-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {s.connected ? (
                      <CheckCircle size={14} className="text-emerald-400 flex-shrink-0" />
                    ) : (
                      <AlertCircle size={14} className="text-red-400 flex-shrink-0" />
                    )}
                    <div>
                      <span className="text-xs font-mono font-bold text-foreground">{s.name}</span>
                      <span className="text-[9px] font-mono text-muted-foreground/50 ml-2">{s.transport}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-mono text-muted-foreground">
                      {s.tools_count} tools
                    </span>
                    {!s.connected && (
                      <button
                        onClick={() => handleReconnect(s.name)}
                        disabled={reconnecting === s.name}
                        className="flex items-center gap-1 px-2 py-1 text-[9px] font-mono bg-primary/10 text-primary border border-primary/20 rounded hover:bg-primary/20 transition-colors disabled:opacity-50"
                      >
                        {reconnecting === s.name ? (
                          <Loader2 size={10} className="animate-spin" />
                        ) : (
                          <RefreshCw size={10} />
                        )}
                        重连
                      </button>
                    )}
                  </div>
                </div>
                <p className="text-[9px] font-mono text-muted-foreground/60 mt-1">{s.description}</p>
                {s.connected && s.tools.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {s.tools.map((t) => (
                      <span
                        key={t}
                        className="px-1.5 py-0.5 text-[8px] font-mono bg-primary/10 text-primary/80 border border-primary/20 rounded"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
                {s.error && (
                  <p className="text-[9px] font-mono text-red-400/70 mt-1">错误: {s.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 加载中 */}
      {loading && !status && (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 size={20} className="animate-spin mr-2" />
          <span className="text-xs font-mono">正在连接 brain-core...</span>
        </div>
      )}
    </div>
  )
}

function StatCard({
  label,
  value,
  icon,
  highlight,
}: {
  label: string
  value: number
  icon: React.ReactNode
  highlight?: 'green' | 'yellow'
}) {
  return (
    <div className="bg-card border border-border p-3 rounded-md">
      <div className="flex items-center gap-2 text-muted-foreground/60 mb-1">
        {icon}
        <span className="text-[9px] font-mono">{label}</span>
      </div>
      <div
        className={cn(
          'text-xl font-mono font-bold',
          highlight === 'green' && 'text-emerald-400',
          highlight === 'yellow' && 'text-yellow-400',
          !highlight && 'text-foreground',
        )}
      >
        {value}
      </div>
    </div>
  )
}
