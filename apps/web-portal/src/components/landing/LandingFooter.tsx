import Image from 'next/image'
import Link from 'next/link'

const FOOTER_LINKS = {
  产品: [
    { label: '功能介绍', href: '/features' },
    { label: '定价方案', href: '/pricing' },
    { label: '更新日志', href: '/changelog' },
  ],
  支持: [
    { label: '帮助中心', href: '/help' },
    { label: '联系我们', href: '/contact' },
    { label: '开发者文档', href: '/docs' },
  ],
  法律: [
    { label: '隐私政策', href: '/privacy' },
    { label: '用户协议', href: '/terms' },
    { label: 'Cookie 政策', href: '/cookies' },
  ],
}

export function LandingFooter() {
  return (
    <footer className="border-t border-border bg-card/50">
      {/* 顶部红色渐变线 */}
      <div className="h-px bg-gradient-to-r from-transparent via-primary to-transparent" />

      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          {/* 品牌区 */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="relative w-12 h-12 drop-shadow-[0_0_6px_#FE000060]">
                <Image src="/logo/logo.png" alt="DREAMVFIA" fill sizes="48px" className="object-contain" />
              </div>
              <div>
                <span className="font-display text-sm font-black tracking-[0.2em] text-primary">DREAMVFIA</span>
                <p className="text-xs font-mono text-muted-foreground">梦帮小助 · AI ASSISTANT</p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              三脑并行 AI 助手<br />
              左脑逻辑 · 右脑创意 · 脑干监督
            </p>
          </div>

          {/* 链接列 */}
          {Object.entries(FOOTER_LINKS).map(([title, links]) => (
            <div key={title}>
              <h4 className="text-xs font-mono text-muted-foreground tracking-[0.2em] mb-4">{title}</h4>
              <ul className="space-y-2.5">
                {links.map(({ label, href }) => (
                  <li key={href}>
                    <Link href={href} className="text-sm text-muted-foreground hover:text-primary transition-colors">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* 底部版权 */}
      <div className="border-t border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <span className="text-xs font-mono text-muted-foreground/80">
            © 2026 DREAMVFIA CORP. All rights reserved.
          </span>
          <span className="text-[10px] font-mono text-muted-foreground/60">v3.5.0 · BUILD 20260227</span>
        </div>
      </div>
    </footer>
  )
}
