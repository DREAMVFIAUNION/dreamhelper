'use client'

import { CSSProperties } from 'react'

/** Available PSD icon sets */
export type PsdIconSet =
  | 'psd-simple'    // 32.psd - 43 clean line icons with labels
  | 'psd-classic'   // 11.psd - 70 solid UI icons
  | 'psd-brankic'   // 44.psd - 342 glyph icons (Brankic1979)
  | 'psd-168'       // 35.psd - 170 solid icons
  | 'psd-colorful'  // 33.psd - 81 dual-tone icons
  | 'psd-circle'    // 38.psd - 299 circle outline icons

interface PsdIconProps {
  /** Icon filename without .png extension */
  name: string
  /** Icon set folder, defaults to psd-simple */
  set?: PsdIconSet
  /** Size in pixels, defaults to 20 */
  size?: number
  /** CSS class */
  className?: string
  /** Inline style override */
  style?: CSSProperties
  /** Alt text */
  alt?: string
}

/**
 * PSD-extracted icon component.
 * Uses 48x48 PNG icons from public/icons/{set}/{name}.png
 * 
 * White icons on transparent background — designed for dark themes.
 * Use CSS filter to recolor if needed.
 */
export function PsdIcon({
  name,
  set = 'psd-simple',
  size = 20,
  className = '',
  style,
  alt,
}: PsdIconProps) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={`/icons/${set}/${name}.png`}
      alt={alt || name}
      width={size}
      height={size}
      className={className}
      style={{
        width: size,
        height: size,
        objectFit: 'contain',
        pointerEvents: 'none',
        userSelect: 'none',
        filter: 'brightness(1.3)',
        ...style,
      }}
      draggable={false}
      loading="lazy"
    />
  )
}
