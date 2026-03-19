'use client'

import { cn } from '@/lib/utils'

interface EmotionData {
  mood: string
  valence: number
  arousal: number
  curiosity: number
  confidence: number
  engagement: number
}

interface Props {
  emotion: EmotionData
  size?: number
}

function valenceToHue(valence: number): number {
  // -1 (sad/blue=220) → 0 (neutral/gray=60) → 1 (happy/warm=30)
  if (valence >= 0) return 60 - valence * 30
  return 60 + Math.abs(valence) * 160
}

function arousalToSaturation(arousal: number): number {
  // 0 (calm=30%) → 1 (excited=90%)
  return 30 + arousal * 60
}

function engagementToLightness(engagement: number): number {
  // low=60% → high=50%
  return 60 - engagement * 10
}

export function EmotionIndicator({ emotion, size = 64 }: Props) {
  const hue = valenceToHue(emotion.valence)
  const sat = arousalToSaturation(emotion.arousal)
  const light = engagementToLightness(emotion.engagement)
  const color = `hsl(${hue}, ${sat}%, ${light}%)`

  // Pulse animation intensity based on arousal
  const pulseScale = 1 + emotion.arousal * 0.15

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Color wheel / orb */}
      <div
        className="relative rounded-full flex items-center justify-center"
        style={{ width: size, height: size }}
      >
        {/* Outer glow */}
        <div
          className="absolute inset-0 rounded-full opacity-40 blur-md"
          style={{ backgroundColor: color }}
        />
        {/* Main orb */}
        <div
          className={cn(
            'absolute inset-1 rounded-full transition-all duration-1000',
            'border border-white/10',
          )}
          style={{
            backgroundColor: color,
            transform: `scale(${pulseScale})`,
            boxShadow: `0 0 ${12 + emotion.arousal * 16}px ${color}`,
          }}
        />
        {/* Inner highlight */}
        <div
          className="absolute rounded-full bg-white/20"
          style={{
            width: size * 0.3,
            height: size * 0.3,
            top: size * 0.15,
            left: size * 0.2,
          }}
        />
        {/* Curiosity sparkle ring */}
        {emotion.curiosity > 0.6 && (
          <div
            className="absolute inset-0 rounded-full border border-dashed animate-spin"
            style={{
              borderColor: `hsla(${hue}, ${sat}%, ${light}%, 0.3)`,
              animationDuration: `${8 - emotion.curiosity * 4}s`,
            }}
          />
        )}
      </div>

      {/* Mood label */}
      <span className="text-[10px] font-mono text-muted-foreground">
        {emotion.mood}
      </span>

      {/* Mini dimension bars */}
      <div className="flex gap-0.5">
        {[
          { val: emotion.valence, color: 'bg-green-400', label: 'V' },
          { val: emotion.arousal, color: 'bg-yellow-400', label: 'A' },
          { val: emotion.curiosity, color: 'bg-purple-400', label: 'C' },
          { val: emotion.confidence, color: 'bg-blue-400', label: 'Cf' },
          { val: emotion.engagement, color: 'bg-orange-400', label: 'E' },
        ].map((dim) => (
          <div key={dim.label} className="flex flex-col items-center gap-0.5" title={dim.label}>
            <div className="w-1 h-6 bg-muted/30 rounded-full overflow-hidden flex flex-col-reverse">
              <div
                className={cn('w-full rounded-full transition-all duration-700', dim.color)}
                style={{ height: `${Math.max(0, Math.min(1, (dim.val + 1) / 2)) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
