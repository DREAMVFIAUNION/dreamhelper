/**
 * 梦帮小助 · 字体系统
 * Display: Orbitron (科技感标题)
 * Mono: JetBrains Mono (代码/数据)
 * Body: Inter + Noto Sans SC (正文)
 */

export const fontFamily: Record<string, string[]> = {
  display: ['Orbitron', 'sans-serif'],
  mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
  body: ['Inter', 'Noto Sans SC', 'sans-serif'],
}

export const fontSize: Record<string, [string, Record<string, string>]> = {
  'display-lg': ['2.25rem', { lineHeight: '1.2', fontWeight: '900', letterSpacing: '0.05em' }],
  'display-md': ['1.5rem', { lineHeight: '1.3', fontWeight: '700', letterSpacing: '0.04em' }],
  'display-sm': ['1.125rem', { lineHeight: '1.4', fontWeight: '700', letterSpacing: '0.03em' }],
  'body-lg': ['1rem', { lineHeight: '1.6' }],
  'body-md': ['0.875rem', { lineHeight: '1.6' }],
  'body-sm': ['0.75rem', { lineHeight: '1.5' }],
  'mono-md': ['0.8125rem', { lineHeight: '1.6', letterSpacing: '0.02em' }],
  'mono-sm': ['0.6875rem', { lineHeight: '1.5', letterSpacing: '0.03em' }],
  'mono-xs': ['0.625rem', { lineHeight: '1.4', letterSpacing: '0.05em' }],
}
