import { useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import type { Scholar } from '../types/scholar'
import type { AskEngine } from '../lib/nlSearch'
import { ENGINE_LABELS } from '../lib/nlSearch'
import { scholarAvatarUrl } from '../lib/scholarMedia'
import { subfieldColor } from '../map/colorScale'
import { cx } from '../lib/cx'

// Decorative "searching" view, not real progress: every PI at their position on the map, coloured
// by topic area. Every SHOW_MS a random PI, away from the last one, is shown on their dot as a card
// (photo, name, institution, topic area); one at a time, with a quick fade in and out.
const NARROW_PX = 520
const ASPECT = 0.5 // stage height / width
const ASPECT_NARROW = 0.85 // phones: a taller field, so the map isn't a sliver
const SHOW_MS = 1500 // per PI; keep in sync with the .ask-bloom__chip animation
const CHIP_R = 26 // px, half the chip's height (photo 40 + padding + border); keep in sync with .ask-bloom__chip
const CHIP_W = 260 // px, a chip's typical unrolled width (max-width in .ask-bloom__chip is 280)

interface Bloom {
  key: number
  scholar: Scholar
  color: string
  x: number // dot centre within the stage
  y: number
  dx: number // photo offset from the dot, so the chip stays inside the stage
  dy: number
  side: 'left' | 'right' // which side of the photo the text sits
}

interface AskScanProps {
  scholars: Scholar[]
  engine: AskEngine | null
  waiting: boolean
  status: ReactNode // the live status line, shown in the card's header
}

export function AskScan({ scholars, engine, waiting, status }: AskScanProps) {
  const stageRef = useRef<HTMLDivElement | null>(null)
  const [width, setWidth] = useState(0)
  const [bloom, setBloom] = useState<Bloom | null>(null)
  const [read, setRead] = useState<ReadonlySet<number>>(() => new Set())

  const narrow = width > 0 && width < NARROW_PX
  const height = Math.round(width * (narrow ? ASPECT_NARROW : ASPECT))
  const r = Math.min(3.4, Math.max(2, width / 230))

  // Same orientation as the map view (d3MapController: x right, y down)
  const dots = useMemo(() => {
    if (!width || scholars.length === 0) return []
    const xs = scholars.map((s) => s.x)
    const ys = scholars.map((s) => s.y)
    const [x0, x1] = [Math.min(...xs), Math.max(...xs)]
    const [y0, y1] = [Math.min(...ys), Math.max(...ys)]
    const pad = r * 5 + 2 // room for a match's halo, since the svg clips
    return scholars.map((scholar) => ({
      scholar,
      color: subfieldColor(scholar.subfields[0]?.subfield),
      cx: pad + ((scholar.x - x0) / (x1 - x0 || 1)) * (width - 2 * pad),
      cy: pad + ((scholar.y - y0) / (y1 - y0 || 1)) * (height - 2 * pad),
    }))
  }, [scholars, width, height, r])

  useEffect(() => {
    const stage = stageRef.current
    if (!stage) return
    const observer = new ResizeObserver(([entry]) => setWidth(Math.round(entry.contentRect.width)))
    observer.observe(stage)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (waiting || dots.length === 0) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let cancelled = false
    let key = 0
    let last = { cx: -width, cy: -height }

    // A random PI in a different part of the map from the last one
    const pick = () => {
      let index = 0
      for (let tries = 0; tries < 12; tries++) {
        index = Math.floor(Math.random() * dots.length)
        const { cx: x, cy: y } = dots[index]
        if (Math.abs(y - last.cy) > CHIP_R * 2.6 || (!narrow && Math.abs(x - last.cx) > CHIP_W)) break
      }
      last = dots[index]
      return index
    }

    const spawn = () => {
      const index = pick()
      const { scholar, color, cx: x, cy: y } = dots[index]
      const img = new Image()
      img.src = scholarAvatarUrl(scholar)
      const show = () => {
        if (cancelled) return
        // Text on the side with room; if neither has room (phones), slide the photo off its dot
        const side = x + CHIP_W - CHIP_R <= width ? 'right' : x - CHIP_W + CHIP_R >= 0 ? 'left'
          : x < width / 2 ? 'right' : 'left'
        const fx = side === 'right'
          ? Math.min(Math.max(x, CHIP_R), Math.max(CHIP_R, width - CHIP_W + CHIP_R))
          : Math.max(Math.min(x, width - CHIP_R), Math.min(width - CHIP_R, CHIP_W - CHIP_R))
        const dx = fx - x
        const dy = Math.min(Math.max(y, CHIP_R + 4), height - CHIP_R - 4) - y
        setBloom({ key: ++key, scholar, color, x, y, dx, dy, side })
        setRead((prev) => new Set(prev).add(index))
      }
      img.decode().then(show, show)
    }

    spawn()
    const interval = window.setInterval(spawn, SHOW_MS)
    return () => {
      cancelled = true
      window.clearInterval(interval)
      setBloom(null)
    }
  }, [waiting, dots, width, height, narrow])

  if (scholars.length === 0) return null

  return (
    <div className={cx('ask-scan', waiting && 'is-waiting')}>
      <div className="ask-scan__head">
        <p className="ask-scan__status">{status}</p>
        {engine && (
          <span className="ask-scan__engine">
            via <b>{ENGINE_LABELS[engine]}</b>
          </span>
        )}
      </div>
      <div ref={stageRef} className="ask-scan__stage" style={{ height: height || undefined }} aria-hidden="true">
        {width > 0 && (
          <svg className="ask-scan__map" width={width} height={height}>
            <g className="ask-scan__dots">
              {dots.map((d, i) => (
                <circle
                  key={d.scholar.id}
                  className={cx(read.has(i) && 'is-read')}
                  cx={d.cx}
                  cy={d.cy}
                  r={r}
                  fill={d.color}
                />
              ))}
            </g>
          </svg>
        )}
        {bloom && [bloom].map((b) => (
          <div
            key={b.key}
            className={cx('ask-bloom', `ask-bloom--${b.side}`)}
            style={{ left: b.x, top: b.y, '--c': b.color, '--dx': `${b.dx}px`, '--dy': `${b.dy}px` } as CSSProperties}
          >
            <div className="ask-bloom__chip">
              <img className="ask-bloom__face" src={scholarAvatarUrl(b.scholar)} alt="" />
              <span className="ask-bloom__text">
                <span className="ask-bloom__name">{b.scholar.name}</span>
                {b.scholar.institution && <span className="ask-bloom__inst">{b.scholar.institution}</span>}
                {b.scholar.subfields[0]?.subfield && <span className="ask-bloom__field">{b.scholar.subfields[0].subfield}</span>}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
