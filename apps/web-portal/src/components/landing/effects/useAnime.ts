'use client'

import { useEffect, useRef, useCallback } from 'react'

/**
 * useAnime — anime.js lifecycle hook for React
 * Returns a stable ref callback. Call setup(el) inside useEffect;
 * cleanup is automatic on unmount.
 */
export function useAnimeRef<T extends HTMLElement | SVGElement>() {
  const ref = useRef<T | null>(null)
  const cleanupRef = useRef<(() => void) | null>(null)

  const setCleanup = useCallback((fn: () => void) => {
    cleanupRef.current = fn
  }, [])

  useEffect(() => {
    return () => {
      cleanupRef.current?.()
    }
  }, [])

  return { ref, setCleanup }
}

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}
