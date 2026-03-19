/**
 * 梦帮小助 · 阴影系统（红色霓虹光晕）
 */

export const boxShadow = {
  'red-glow': '0 0 15px #FE000030, 0 0 30px #FE000015',
  'red-glow-lg': '0 0 25px #FE000040, 0 0 50px #FE000020',
  'red-glow-intense': '0 0 20px #FE000060, 0 0 40px #FE000030, 0 0 80px #FE000015',
  card: '0 2px 8px #00000060',
  'card-hover': '0 4px 16px #00000080, 0 0 10px #FE000015',
  panel: '0 4px 24px #000000A0',
  inner: 'inset 0 1px 4px #000000A0',
} as const

export const dropShadow = {
  'neon-red': '0 0 10px #FE000080',
  'neon-red-lg': '0 0 20px #FE000080',
} as const
