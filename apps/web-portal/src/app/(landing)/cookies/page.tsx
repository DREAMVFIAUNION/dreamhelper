'use client'

import { motion } from 'framer-motion'

const COOKIE_TYPES = [
  {
    name: '必要 Cookie',
    tag: '始终启用',
    items: [
      { cookie: 'token', purpose: 'JWT 登录凭证，维持用户会话', duration: '7 天' },
      { cookie: 'locale', purpose: '用户语言偏好（zh-CN / en）', duration: '30 天' },
    ],
  },
  {
    name: '功能性 Cookie',
    tag: '默认启用',
    items: [
      { cookie: 'dreamhelp_theme', purpose: '界面主题偏好（暗色/亮色）', duration: '30 天' },
      { cookie: 'dreamhelp_sidebar', purpose: '侧边栏展开/收起状态', duration: '会话' },
      { cookie: 'dreamhelp_pwa_dismissed', purpose: 'PWA 安装提示关闭状态', duration: '7 天' },
    ],
  },
  {
    name: '分析 Cookie',
    tag: '暂未使用',
    items: [
      { cookie: '—', purpose: '目前我们未使用任何第三方分析 Cookie（如 Google Analytics）。如未来启用，将提前告知并提供退出选项。', duration: '—' },
    ],
  },
]

export default function CookiesPage() {
  return (
    <div className="pt-24 pb-20">
      <div className="max-w-4xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <p className="text-xs font-mono text-primary tracking-[0.3em] mb-2">COOKIE POLICY</p>
          <h1 className="text-3xl md:text-5xl font-display font-bold">Cookie 政策</h1>
          <p className="mt-4 text-sm text-muted-foreground">最后更新：2026 年 2 月 26 日</p>
          <div className="mt-4 mx-auto w-20 h-px bg-gradient-to-r from-transparent via-primary to-transparent" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <div className="p-6 bg-card border border-border rounded-lg mb-8">
            <h2 className="text-base font-bold mb-3">什么是 Cookie？</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Cookie 是网站存储在您浏览器中的小型文本文件，用于记住您的偏好、维持登录状态等。
              梦帮小助使用尽可能少的 Cookie，仅保留服务运行所必需的项目。
            </p>
          </div>

          <div className="space-y-8">
            {COOKIE_TYPES.map((type, i) => (
              <motion.div
                key={type.name}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * i }}
                className="p-6 bg-card border border-border rounded-lg"
              >
                <div className="flex items-center gap-3 mb-4">
                  <h2 className="text-base font-bold">{type.name}</h2>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-primary/10 text-primary">
                    {type.tag}
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left">
                        <th className="pb-2 font-mono text-xs text-muted-foreground font-normal w-1/4">Cookie</th>
                        <th className="pb-2 font-mono text-xs text-muted-foreground font-normal">用途</th>
                        <th className="pb-2 font-mono text-xs text-muted-foreground font-normal w-1/5">有效期</th>
                      </tr>
                    </thead>
                    <tbody>
                      {type.items.map((item) => (
                        <tr key={item.cookie} className="border-b border-border/50 last:border-0">
                          <td className="py-2.5 font-mono text-xs text-primary">{item.cookie}</td>
                          <td className="py-2.5 text-muted-foreground text-xs">{item.purpose}</td>
                          <td className="py-2.5 text-muted-foreground text-xs">{item.duration}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="mt-8 p-6 bg-card border border-border rounded-lg">
            <h2 className="text-base font-bold mb-3">管理 Cookie</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              您可以通过浏览器设置随时查看、删除或禁用 Cookie。请注意，禁用必要 Cookie 可能导致您无法正常登录和使用服务。
            </p>
            <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
              <li>• Chrome：设置 → 隐私和安全 → Cookie</li>
              <li>• Firefox：设置 → 隐私与安全 → Cookie</li>
              <li>• Safari：偏好设置 → 隐私</li>
              <li>• Edge：设置 → Cookie 和网站权限</li>
            </ul>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
