import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-8">
      <div className="text-center space-y-4">
        <div className="text-6xl font-display font-bold text-primary tracking-widest">404</div>
        <h1 className="text-lg font-mono font-bold text-foreground">页面未找到</h1>
        <p className="text-xs font-mono text-muted-foreground max-w-sm">
          你访问的页面不存在或已被移除。请检查 URL 是否正确。
        </p>
        <div className="flex gap-3 justify-center pt-4">
          <Link
            href="/"
            className="px-5 py-2 bg-primary text-primary-foreground font-mono font-bold text-xs rounded-md hover:bg-primary/90 transition-colors"
          >
            返回首页
          </Link>
          <Link
            href="/overview"
            className="px-5 py-2 border border-border text-foreground font-mono text-xs rounded-md hover:border-primary/40 transition-colors"
          >
            控制面板
          </Link>
        </div>
      </div>
      <div className="mt-12 text-[9px] font-mono text-muted-foreground/30">
        DREAMHELP v3.0 · PAGE_NOT_FOUND
      </div>
    </div>
  )
}
