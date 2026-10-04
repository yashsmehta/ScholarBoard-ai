import { useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import type { Scholar } from '../types/scholar'
import type { AskEngine, AskSteps } from '../lib/nlSearch'
import { ENGINE_LABELS } from '../lib/nlSearch'
import { scholarAvatarUrl } from '../lib/scholarMedia'
import { subfieldColor } from '../map/colorScale'
import { cx } from '../lib/cx'

// The "searching" view. Real progress: the agent's steps as its tools report them (filter, shortlist)
// and a time bar against the engine's recent median run time. Decorative: every PI at their position
// on the map, coloured by topic area; every SHOW_MS a random PI, away from the last one, is shown on
// their dot as a card (photo, name, institution, topic area), one at a time with a quick fade.
const NARROW_PX = 520
const ASPECT = 0.5 // stage height / width
const ASPECT_NARROW = 0.72 // narrow stages: a taller field, so the map isn't a sliver
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

/** A running search as the client has seen it (AskPanel polls the server). */
export interface AskRun {
  startedAt: number // client clock, when the server first reported it running
  expectedSeconds: number | null
  steps: AskSteps | null
  filteredAt: number | null // client clock, when each step was first seen
  shortlistAt: number | null
}

interface AskScanProps {
  scholars: Scholar[]
  engine: AskEngine | null
  waiting: boolean
  status: ReactNode // the live status line, shown in the card's header
  run: AskRun | null
  now: number
}

type StepState = 'done' | 'active' | 'todo'

interface Step {
  key: string
  state: StepState
  title: string
  note?: string
}

/** Share of the run that is done: elapsed time against the expected run time, linear up to 90% at
 *  the expected time and then creeping towards 98%, never behind what the steps show. */
function progressOf(run: AskRun | null, now: number): number {
  if (!run) return 0
  const t = (now - run.startedAt) / 1000
  const e = run.expectedSeconds ?? 45
  const byTime = t <= e ? 0.9 * (t / e) : 0.9 + 0.08 * (1 - Math.exp(-(t - e) / (0.5 * e)))
  const floor = run.steps?.shortlist != null ? 0.55 : run.steps?.filtered ? 0.15 : 0.03
  return Math.max(byTime, floor)
}

function timeLeft(run: AskRun | null, now: number): string {
  if (!run?.expectedSeconds) return ''
  const left = run.expectedSeconds - (now - run.startedAt) / 1000
  if (left > 7) return `about ${Math.ceil(left / 5) * 5} s left`
  if (left > -10) return 'a few seconds left'
  return 'almost there'
}

function stepsOf(run: AskRun | null, total: number, waiting: boolean): Step[] {
  const at = (ms: number | null) => (run && ms != null ? `at ${Math.max(1, Math.round((ms - run.startedAt) / 1000))} s` : undefined)
  const s = run?.steps
  const started = run != null && !waiting
  const pool = s?.filtered && s.eligible != null ? s.eligible : total
  const shortlisted = s?.shortlist != null
  const steps: Step[] = [
    { key: 'read', state: started ? 'done' : 'active', title: started ? 'Read your request' : 'Waiting to start' },
  ]
  if (s?.filtered) {
    steps.push({ key: 'filter', state: 'done', title: `Filtered to ${pool.toLocaleString()} eligible PIs`, note: at(run!.filteredAt) })
  }
  steps.push(
    shortlisted
      ? { key: 'scan', state: 'done', title: `Shortlisted ${s!.shortlist} of ${pool.toLocaleString()} PIs`, note: at(run!.shortlistAt) }
      : { key: 'scan', state: started ? 'active' : 'todo', title: `Scanning ${pool.toLocaleString()} PI profiles`, note: started ? 'Shortlisting anyone who fits' : undefined },
    shortlisted
      ? { key: 'read-deep', state: 'active', title: 'Reading their papers', note: 'Weighing topic, methods, species' }
      : { key: 'read-deep', state: 'todo', title: 'Read the shortlist in depth' },
    { key: 'rank', state: 'todo', title: 'Rank the top 10' },
  )
  return steps
}

export function AskScan({ scholars, engine, waiting, status, run, now }: AskScanProps) {
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

  const progress = waiting ? 0 : progressOf(run, now)
  const steps = stepsOf(run, scholars.length, waiting)
  const left = waiting ? '' : timeLeft(run, now)

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
      <div className="ask-scan__progress">
        <div
          className="ask-scan__bar"
          role="progressbar"
          aria-label="Search progress (estimated)"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(progress * 100)}
        >
          <span style={{ transform: `scaleX(${progress})` }} />
        </div>
        <span className="ask-scan__left">{left}</span>
      </div>
      <div className="ask-scan__body">
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
        <ol className="ask-steps" aria-label="What the agent is doing">
          {steps.map((step) => (
            <li key={step.key} className={`ask-steps__item is-${step.state}`}>
              <span className="ask-steps__mark" aria-hidden="true">
                {step.state === 'done' && (
                  <svg viewBox="0 0 12 12"><path d="M2.5 6.2 5 8.6l4.6-5" /></svg>
                )}
              </span>
              <span className="ask-steps__text">
                <span className="ask-steps__title">{step.title}</span>
                {step.note && <span className="ask-steps__note">{step.note}</span>}
              </span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
