import { useEffect, useRef, useState } from 'react'
import type { Scholar } from '../types/scholar'
import type { AskEngine, AskResult } from '../lib/nlSearch'
import { ENGINE_LABELS, fetchEngines, runAskSearch } from '../lib/nlSearch'
import { SPINNER_VERBS } from '../lib/spinnerVerbs'
import { ListAvatar } from './ScholarList'
import { cx } from '../lib/cx'

interface AskPanelProps {
  open: boolean
  scholars: Scholar[]
  results: AskResult[] | null
  selectedScholarId: string | null
  onResults: (results: AskResult[] | null) => void
  onRunningChange: (running: boolean) => void
  onSelectScholar: (scholarId: string) => void
}

const EXAMPLES = [
  'Who would be the best reviewers for this abstract?\n\n',
  'Labs combining fMRI with deep neural network models of object recognition',
  'Early-career PIs in Europe working on visual crowding or peripheral vision',
  'Researchers similar to Talia Konkle but focused on infant development',
]

const MOD_KEY = /Mac|iPhone|iPad/.test(navigator.userAgent) ? '⌘' : 'Ctrl'
// Claude Code's status-line sparkle cycle (same as aos-ai); the verb changes every VERB_SECONDS.
const STARS = ['·', '✻', '✽', '✶', '*']
const VERB_SECONDS = 8
const ENGINE_KEY = 'sb_ai_engine'

function storedEngine(): AskEngine | null {
  try {
    return localStorage.getItem(ENGINE_KEY) as AskEngine | null
  } catch {
    return null
  }
}

type Phase =
  | { kind: 'idle' }
  | { kind: 'running'; startedAt: number; queuePosition: number; seed: number }
  | { kind: 'error'; message: string }

declare global {
  interface Window {
    goatcounter?: { count: (vars: { path: string; title?: string; event?: boolean }) => void }
  }
}

export function AskPanel({
  open,
  scholars,
  results,
  selectedScholarId,
  onResults,
  onRunningChange,
  onSelectScholar,
}: AskPanelProps) {
  const [query, setQuery] = useState('')
  const [phase, setPhase] = useState<Phase>({ kind: 'idle' })
  const [now, setNow] = useState(() => Date.now())
  const [engines, setEngines] = useState<AskEngine[]>([])
  const [engine, setEngine] = useState<AskEngine>(() => storedEngine() ?? 'agy')
  const abortRef = useRef<AbortController | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  const running = phase.kind === 'running'
  const byId = new Map(scholars.map((s) => [s.id, s]))

  useEffect(() => {
    onRunningChange(running)
  }, [running, onRunningChange])

  useEffect(() => {
    if (!running) return
    const timer = setInterval(() => setNow(Date.now()), 260)
    return () => clearInterval(timer)
  }, [running])

  useEffect(() => {
    if (open && results == null && !running) textareaRef.current?.focus()
  }, [open, results, running])

  useEffect(() => () => abortRef.current?.abort(), [])

  useEffect(() => {
    if (!open || engines.length) return
    void fetchEngines().then((list) => {
      setEngines(list)
      if (list.length) setEngine((current) => (list.includes(current) ? current : list[0]))
    })
  }, [open, engines.length])

  function chooseEngine(next: AskEngine) {
    setEngine(next)
    try {
      localStorage.setItem(ENGINE_KEY, next)
    } catch {
      /* per-browser convenience only */
    }
  }

  async function submit() {
    const q = query.trim()
    if (q.length < 3 || running) return
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    onResults(null)
    setNow(Date.now())
    setPhase({ kind: 'running', startedAt: Date.now(), queuePosition: 0, seed: Math.floor(Math.random() * SPINNER_VERBS.length) })
    window.goatcounter?.count({ path: 'ai-search', title: 'AI search', event: true })
    try {
      const found = await runAskSearch(
        q,
        engine,
        (p) => setPhase((prev) =>
          prev.kind === 'running' ? { ...prev, queuePosition: p.status === 'queued' ? p.queuePosition + 1 : 0 } : prev),
        controller.signal,
      )
      onResults(found)
      setPhase({ kind: 'idle' })
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return
      setPhase({ kind: 'error', message: error instanceof Error ? error.message : 'Search failed — please try again.' })
    }
  }

  function cancel() {
    abortRef.current?.abort()
    setPhase({ kind: 'idle' })
  }

  function fill(text: string) {
    setQuery(text)
    requestAnimationFrame(() => {
      const el = textareaRef.current
      if (!el) return
      el.focus()
      el.setSelectionRange(text.length, text.length)
    })
  }

  const elapsedMs = running ? Math.max(0, now - phase.startedAt) : 0
  const elapsed = Math.floor(elapsedMs / 1000)
  const star = STARS[Math.floor(elapsedMs / 260) % STARS.length]
  const verb = running ? SPINNER_VERBS[(phase.seed + Math.floor(elapsed / VERB_SECONDS) * 37) % SPINNER_VERBS.length] : ''

  return (
    <section className={cx('ask', !open && 'ask--hidden')} id="ws-panel-ai" role="tabpanel" aria-labelledby="ws-tab-ai" hidden={!open}>
      <div className="ask__inner">
        <header className="ask__head">
          <div>
            <h2 className="ask__title">Find researchers by what they study</h2>
            <p className="ask__lede">
              Describe a topic or method, or paste an abstract to find reviewers. Every PI profile is read and the ten
              closest matches are ranked.
            </p>
          </div>
        </header>

        <form
          className="ask__form"
          onSubmit={(e) => {
            e.preventDefault()
            void submit()
          }}
        >
          <textarea
            ref={textareaRef}
            className="ask__input"
            value={query}
            rows={query.length > 160 ? 8 : 3}
            maxLength={6000}
            placeholder="e.g. Who studies how attention modulates crowding with EEG?"
            aria-label="Describe who you are looking for"
            disabled={running}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                void submit()
              }
            }}
          />
          <div className="ask__actions">
            {engines.length > 1 && (
              <div className="ask__engine" role="radiogroup" aria-label="Search engine">
                {engines.map((e) => (
                  <button
                    key={e}
                    type="button"
                    role="radio"
                    aria-checked={engine === e}
                    className={cx(engine === e && 'is-active')}
                    disabled={running}
                    onClick={() => chooseEngine(e)}
                  >
                    {ENGINE_LABELS[e]}
                  </button>
                ))}
              </div>
            )}
            <span className="ask__hint">{MOD_KEY} + Enter</span>
            {running ? (
              <button type="button" className="ask__button ask__button--quiet" onClick={cancel}>Cancel</button>
            ) : (
              <button type="submit" className="ask__button" disabled={query.trim().length < 3}>Search</button>
            )}
          </div>
        </form>

        {phase.kind === 'idle' && results == null && (
          <div className="ask__examples">
            <p className="ask__label">For example</p>
            <ul>
              {EXAMPLES.map((ex) => (
                <li key={ex}>
                  <button type="button" onClick={() => fill(ex)}>{ex.trim()}</button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {running && (
          <div className="ask__status" role="status" aria-live="polite">
            <p className="ask__spinner">
              <span className="ask__star" aria-hidden="true">{star}</span>
              {phase.queuePosition > 0 ? `Waiting for a free slot (#${phase.queuePosition})` : `${verb}…`}
              <span className="ask__time"> ({elapsed}s)</span>
            </p>
            <p className="ask__note">
              {ENGINE_LABELS[engine]} is reading all {scholars.length || ''} profiles.{' '}
              {engine === 'claude' ? 'Usually about 20 seconds.' : 'Usually 1–2 minutes.'}
            </p>
          </div>
        )}

        {phase.kind === 'error' && (
          <p className="ask__error" role="alert">
            {phase.message}{' '}
            <button type="button" onClick={() => void submit()}>Try again</button>
          </p>
        )}

        {results != null && (
          <div className="ask__results">
            <div className="ask__results-head">
              <p className="ask__label">{results.length ? `${results.length} matches, best first` : 'No close matches'}</p>
              <button type="button" className="ask__link" onClick={() => { onResults(null); fill('') }}>
                Clear
              </button>
            </div>
            {results.length === 0 && (
              <p className="ask__note">Nobody in the directory is a plausible fit. Try describing the topic or methods differently.</p>
            )}
            <ol className="ask__list">
              {results.map((r, i) => {
                const scholar = byId.get(r.id)
                return scholar && (
                  <li key={r.id}>
                    <button
                      type="button"
                      className={cx('ask-row', r.id === selectedScholarId && 'is-selected')}
                      onClick={() => onSelectScholar(r.id)}
                    >
                      <span className="ask-row__rank">{i + 1}</span>
                      <ListAvatar scholar={scholar} />
                      <span className="ask-row__body">
                        <span className="ask-row__name">{scholar.name}</span>
                        {scholar.institution && <span className="ask-row__inst">{scholar.institution}</span>}
                        <span className="ask-row__why">{r.reason}</span>
                      </span>
                    </button>
                  </li>
                )
              })}
            </ol>
            {results.length > 0 && (
              <p className="ask__foot">Ranked by a language model from public profiles and recent papers. Worth a quick check.</p>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
