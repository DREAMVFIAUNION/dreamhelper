import type { BrainPhase } from '@/hooks/useStreamChat'
import type { AvatarState } from './avatar.types'

/** Sprite 文件映射 */
export const SPRITE_MAP: Record<AvatarState, string> = {
  idle:      '/avatar/idle.webp',
  listening: '/avatar/listening.webp',
  thinking:  '/avatar/thinking.webp',
  speaking:  '/avatar/greeting.webp',
  greeting:  '/avatar/greeting.webp',
  error:     '/avatar/thinking.webp',
}

/** CSS 动画 class 映射 */
export const ANIMATION_MAP: Record<AvatarState, string> = {
  idle:      'animate-breathe',
  listening: 'animate-lean-forward',
  thinking:  'animate-think-shake',
  speaking:  'animate-speak-bounce',
  greeting:  'animate-wave',
  error:     'animate-error-flash',
}

/** BrainPhase → AvatarState 映射 */
export const PHASE_TO_AVATAR: Record<BrainPhase, AvatarState> = {
  'idle':                'idle',
  'thalamus_routing':    'listening',
  'thalamus_done':       'thinking',
  'brainstem_responding': 'speaking',
  'brainstem_analyzing': 'thinking',
  'cortex_activating':   'thinking',
  'thinking':            'thinking',
  'left_done':           'thinking',
  'right_done':          'thinking',
  'brainstem_directive': 'thinking',
  'fusing':              'thinking',
  'brainstem_reviewing': 'speaking',
  'done':                'greeting',
}

/** 状态文字 */
export const STATUS_TEXT: Record<AvatarState, string> = {
  idle:      '',
  listening: '正在听...',
  thinking:  '思考中...',
  speaking:  '回答中',
  greeting:  '✨',
  error:     '出了点问题',
}

/** 脑区详情文字 */
export const BRAIN_STATUS_TEXT: Partial<Record<BrainPhase, string>> = {
  'thalamus_routing':    '丘脑路由中...',
  'cortex_activating':   '皮层激活...',
  'brainstem_analyzing': '脑干分析...',
  'thinking':            '深度思考...',
  'fusing':              '前额叶融合...',
  'brainstem_reviewing': '质量审查...',
}

/** greeting 状态持续时间(ms)，之后回到 idle */
export const GREETING_DURATION = 3000

/** 默认头像尺寸 */
export const DEFAULT_AVATAR_SIZE = 240
