import { useEffect, useState } from 'react'
import { cx } from '../lib/cx'

interface MapControlsProps {
  onReset: () => void
}

export function MapControls({ onReset }: MapControlsProps) {
  const [hintHidden, setHintHidden] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setHintHidden(true), 4000)
    return () => clearTimeout(timer)
  }, [])

  return (
    <>
      <div className="map-overlay map-overlay-bottom-left">
        <p className={cx('map-hint', hintHidden && 'map-hint--hidden')}>
          Scroll to zoom &middot; Drag or arrow keys to pan &middot; Click a dot
        </p>
      </div>
      <div className="map-overlay map-overlay-bottom-right">
        <div className="map-controls">
          <button type="button" className="icon-button" onClick={onReset}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path
                d="M13.5 8a5.5 5.5 0 0 1-9.4 3.9M2.5 8a5.5 5.5 0 0 1 9.4-3.9"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
              <path
                d="M4.1 14.5V11.9H1.5M11.9 1.5v2.6h2.6"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Reset View
          </button>
        </div>
      </div>
    </>
  )
}
