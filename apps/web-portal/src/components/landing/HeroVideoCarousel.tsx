'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

const VIDEOS = ['/videos/hero-1.mp4', '/videos/hero-2.mp4', '/videos/hero-3.mp4']

export function HeroVideoCarousel() {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [fading, setFading] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  const playNext = useCallback(() => {
    setFading(true)
    setTimeout(() => {
      setCurrentIdx((prev) => (prev + 1) % VIDEOS.length)
      setFading(false)
    }, 800)
  }, [])

  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    video.load()
    video.play().catch(() => {})
  }, [currentIdx])

  return (
    <div className="absolute inset-0 w-full h-full overflow-hidden">
      {/* 16:9 视频 — object-cover 填满全屏 */}
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover transition-opacity duration-700"
        style={{ opacity: fading ? 0 : 1, aspectRatio: '16/9' }}
        src={VIDEOS[currentIdx]}
        muted
        autoPlay
        playsInline
        onEnded={playNext}
      />

      {/* 暗色叠加层 — 保证前景文字可读 */}
      <div className="absolute inset-0 bg-black/50" />
    </div>
  )
}
