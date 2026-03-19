/**
 * 梦帮小助 · 赛博朋克色彩系统
 * 品牌红取自 DREAMVFIA LOGO (#FE0000)
 */

export const colors = {
  brand: {
    DEFAULT: '#FE0000',
    dark: '#CC0000',
    light: '#FF3333',
  },

  bg: {
    void: '#000000',
    base: '#080808',
    deep: '#050505',
    surface: '#121215',
    elevated: '#1A1A1F',
    panel: '#151518',
  },

  border: {
    DEFAULT: '#2A2A2E',
    subtle: '#1E1E22',
    accent: '#FE000050',
    glow: '#FE000070',
  },

  text: {
    primary: '#F0F0F0',
    secondary: '#C0C0C0',
    muted: '#808088',
    inverse: '#080808',
  },

  cyber: {
    green: '#00FF88',
    blue: '#00BFFF',
    amber: '#FFB800',
    purple: '#8B5CF6',
  },

  status: {
    success: '#00FF88',
    warning: '#FFB800',
    error: '#FE0000',
    info: '#00BFFF',
  },
} as const

export type Colors = typeof colors
