'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { PsdIcon, type PsdIconSet } from '@/components/ui/PsdIcon'

interface MenuItem {
  label: string
  icon: string
  iconSet: PsdIconSet
  href: string
}

const menuGroups: { title: string; items: MenuItem[] }[] = [
  {
    title: '总览',
    items: [
      { label: '数据面板', icon: 'graph_chart', iconSet: 'psd-brankic', href: '/admin' },
      { label: '数据分析', icon: 'chart_pie', iconSet: 'psd-brankic', href: '/admin/analytics' },
    ],
  },
  {
    title: '业务管理',
    items: [
      { label: '用户管理', icon: 'friends', iconSet: 'psd-simple', href: '/admin/users' },
      { label: '组织管理', icon: 'sitemap_1', iconSet: 'psd-brankic', href: '/admin/organizations' },
      { label: '对话管理', icon: 'comments', iconSet: 'psd-simple', href: '/admin/sessions' },
      { label: '智能体管理', icon: 'marvin', iconSet: 'psd-brankic', href: '/admin/agents' },
      { label: '知识库管理', icon: 'encyclopedia', iconSet: 'psd-classic', href: '/admin/knowledge' },
      { label: '技能管理', icon: 'award_ribbon', iconSet: 'psd-brankic', href: '/admin/skills' },
    ],
  },
  {
    title: '系统',
    items: [
      { label: '审计日志', icon: 'drafts', iconSet: 'psd-simple', href: '/admin/audit' },
      { label: '邮件营销', icon: 'letter', iconSet: 'psd-simple', href: '/admin/email' },
      { label: 'MCP 服务', icon: 'connect', iconSet: 'psd-brankic', href: '/admin/mcp' },
      { label: '工作人员', icon: 'account', iconSet: 'psd-simple', href: '/admin/staff' },
      { label: '系统设置', icon: 'setting', iconSet: 'psd-simple', href: '/admin/system' },
    ],
  },
]

export function AdminSidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-60 bg-card border-r border-border flex flex-col h-full">
      {/* 顶部标识 */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary/20 border border-primary/40 flex items-center justify-center text-primary font-mono text-xs font-bold rounded-md">
            D
          </div>
          <div>
            <div className="text-xs font-mono font-bold text-foreground">
              DREAMVFIA
            </div>
            <div className="text-[10px] font-mono text-primary tracking-widest">
              ADMIN CONSOLE
            </div>
          </div>
        </div>
      </div>

      {/* 菜单 */}
      <nav className="flex-1 overflow-y-auto py-2">
        {menuGroups.map((group) => (
          <div key={group.title} className="mb-2">
            <div className="px-4 py-1.5 text-[10px] font-mono text-muted-foreground/60 tracking-widest uppercase">
              {group.title}
            </div>
            {group.items.map((item) => {
              const isActive =
                item.href === '/admin'
                  ? pathname === '/admin'
                  : pathname.startsWith(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2.5 mx-2 px-3 py-2 text-xs font-mono rounded transition-all ${
                    isActive
                      ? 'bg-primary/10 text-primary border-l-2 border-primary'
                      : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
                  }`}
                >
                  <PsdIcon name={item.icon} set={item.iconSet} size={16} className="shrink-0 opacity-80" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
        ))}
      </nav>

      {/* 底部快捷入口 */}
      <div className="border-t border-border p-3 space-y-1">
        <Link
          href="/overview"
          className="flex items-center gap-2 px-2 py-1.5 text-[11px] font-mono text-muted-foreground hover:text-primary hover:bg-secondary rounded transition-colors"
        >
          <PsdIcon name="browser" set="psd-brankic" size={14} className="opacity-70" /> 用户工作台
        </Link>
        <a
          href="/"
          className="flex items-center gap-2 px-2 py-1.5 text-[11px] font-mono text-muted-foreground hover:text-primary hover:bg-secondary rounded transition-colors"
        >
          <PsdIcon name="update" set="psd-simple" size={14} className="opacity-70" /> 门户首页
        </a>
      </div>
    </aside>
  )
}
