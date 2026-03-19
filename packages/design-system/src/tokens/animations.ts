/**
 * 梦帮小助 · 动效系统
 */

export const keyframes = {
  flicker: {
    '0%, 100%': { opacity: '1' },
    '41.99%': { opacity: '1' },
    '42%': { opacity: '0.6' },
    '43%': { opacity: '0.2' },
    '43.5%': { opacity: '0.8' },
    '44%': { opacity: '1' },
    '80%': { opacity: '1' },
    '80.5%': { opacity: '0.5' },
    '81%': { opacity: '1' },
  },
  'pulse-red': {
    '0%, 100%': { boxShadow: '0 0 8px #FE000040' },
    '50%': { boxShadow: '0 0 20px #FE000080' },
  },
  'scan-line': {
    '0%': { top: '0%' },
    '100%': { top: '100%' },
  },
  dataStream: {
    '0%': { transform: 'translateX(-100%)' },
    '100%': { transform: 'translateX(100%)' },
  },
  glitch: {
    '0%': { transform: 'translate(0)' },
    '20%': { transform: 'translate(-2px, 2px)' },
    '40%': { transform: 'translate(-2px, -2px)' },
    '60%': { transform: 'translate(2px, 2px)' },
    '80%': { transform: 'translate(2px, -2px)' },
    '100%': { transform: 'translate(0)' },
  },
  fadeIn: {
    '0%': { opacity: '0', transform: 'translateY(4px)' },
    '100%': { opacity: '1', transform: 'translateY(0)' },
  },
} as const

export const animation = {
  flicker: 'flicker 4s infinite',
  'pulse-red': 'pulse-red 2s ease-in-out infinite',
  'scan-line': 'scan-line 3s linear infinite',
  'data-stream': 'dataStream 1.5s linear infinite',
  glitch: 'glitch 0.3s steps(2) infinite',
  'fade-in': 'fadeIn 0.3s ease-out',
} as const
