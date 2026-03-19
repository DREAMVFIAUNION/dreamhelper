import type { Config } from 'tailwindcss'
import { colors } from '../tokens/colors'
import { fontFamily, fontSize } from '../tokens/typography'
import { boxShadow, dropShadow } from '../tokens/shadows'
import { keyframes, animation } from '../tokens/animations'

/**
 * 梦帮小助 · TailwindCSS 赛博朋克预设
 * 在 apps/web-portal/tailwind.config.ts 中通过 presets: [cyberpunkPreset] 引入
 */
const cyberpunkPreset: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        brand: colors.brand,
        bg: colors.bg,
        border: colors.border,
        text: colors.text,
        cyber: colors.cyber,
        status: colors.status,
      },
      borderColor: {
        DEFAULT: colors.border.DEFAULT,
        border: colors.border,
        brand: colors.brand,
        subtle: colors.border.subtle,
        accent: colors.border.accent,
        glow: colors.border.glow,
      },
      fontFamily,
      fontSize,
      boxShadow,
      dropShadow,
      keyframes,
      animation,
      backgroundImage: {
        'grid-cyber':
          'linear-gradient(#FE000008 1px, transparent 1px), linear-gradient(90deg, #FE000008 1px, transparent 1px)',
        scanline:
          'repeating-linear-gradient(0deg, transparent, transparent 2px, #00000015 2px, #00000015 4px)',
      },
      backgroundSize: {
        'grid-cyber': '40px 40px',
      },
    },
  },
}

export default cyberpunkPreset
