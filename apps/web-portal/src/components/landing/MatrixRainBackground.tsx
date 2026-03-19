'use client'

import dynamic from 'next/dynamic'

const MatrixRain = dynamic(
  () => import('./MatrixRain').then(m => ({ default: m.MatrixRain })),
  { ssr: false },
)

/** 全局微弱矩阵雨 — 用于 Server Component layout 中 */
export function MatrixRainBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none">
      <MatrixRain opacity={0.06} speed="slow" density={0.3} />
    </div>
  )
}
