import { useEffect, useMemo, useRef, useState } from 'react'
import type { Scholar } from '../types/scholar'
import type { AskEngine, AskOutcome, AskResult } from '../lib/nlSearch'
import { ENGINE_LABELS, runAskSearch } from '../lib/nlSearch'
import { SPINNER_VERBS } from '../lib/spinnerVerbs'
import { ListAvatar } from './ScholarList'
import { cx } from '../lib/cx'
import { SUBFIELD_COLORS, subfieldColor } from '../map/colorScale'

interface AskPanelProps {
  open: boolean
  scholars: Scholar[]
  results: AskResult[] | null
  selectedScholarId: string | null
  onResults: (results: AskResult[] | null) => void
  onRunningChange: (running: boolean) => void
  onSelectScholar: (scholarId: string) => void
}

const REVIEW_ABSTRACT = 'Artificial neural networks trained on visual tasks develop internal representations resembling those of the primate visual system, a discovery that has guided a decade of computational neuroscience. Research on building brain-aligned models has progressively embraced finer-grained learning objectives, from object classification to contrastive self-supervised objectives that maximize distinctions among individual images. Yet the effect of learning-signal granularity on brain alignment remains largely unexamined. Here we systematically investigate how the granularity of a learning signal shapes representational alignment with human vision. We parametrically vary the number of training classes using a data-driven approach that partitions a set of training images into different numbers of categories via PCA-based splits of pretrained embeddings. We train hundreds of neural networks across convolutional and transformer architectures on these coarse classification tasks and compare their representations with human fMRI responses, macaque electrophysiology recordings, and human behavior. We find that networks trained to distinguish as few as eight broad categories learn representations that match or exceed the neural alignment of models distinguishing 1,000 classes. Even more strikingly, these coarsely trained networks align more closely with human perceptual similarity judgments than all other models evaluated, including networks trained with fine-grained supervision or self-supervision as well as leading large-scale vision models. These results demonstrate that human-like visual representations can emerge from surprisingly simple learning objectives, reframing what learning signals vision may require and opening a path toward building AI systems that are more aligned with human perception.'

// label is what the list shows; text is what a click puts in the box.
const EXAMPLES = [
  { label: 'Who would be the best reviewers for this abstract?', text: `Who would be the best reviewers for this abstract?\n\n${REVIEW_ABSTRACT}` },
  'Labs using layer-resolved 7T fMRI or laminar recordings to separate feedforward from feedback signals in early visual cortex',
  'Labs in the Northeastern U.S. recording intracranially (sEEG/ECoG) from patients during visual recognition tasks',
  'Who studies whether microsaccades and fixational drift actively shape what we see at the fovea?',
].map((ex) => (typeof ex === 'string' ? { label: ex, text: ex } : ex))

// Searching animation: one dot per PI, grouped by topic area, with a light sweeping across.
const SCAN_ROWS = 12
const SCAN_PERIOD_S = 2.6
const SUBFIELD_ORDER = new Map(Object.keys(SUBFIELD_COLORS).map((name, i) => [name, i]))

const MOD_KEY = /Mac|iPhone|iPad/.test(navigator.userAgent) ? '⌘' : 'Ctrl'
// Claude Code's status-line sparkle cycle (same as aos-ai); the verb changes every VERB_SECONDS.
const STARS = ['·', '✻', '✽', '✶', '*']
const VERB_SECONDS = 8

type Phase =
  | { kind: 'idle' }
  | { kind: 'running'; startedAt: number; queuePosition: number; seed: number; engine: AskEngine | null }
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
  const [outcome, setOutcome] = useState<Omit<AskOutcome, 'results'> | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  const running = phase.kind === 'running'
  const byId = new Map(scholars.map((s) => [s.id, s]))
  const scanDots = useMemo(() => scholars
    .map((s) => s.subfields[0]?.subfield)
    .sort((a, b) => (SUBFIELD_ORDER.get(a ?? '') ?? 99) - (SUBFIELD_ORDER.get(b ?? '') ?? 99))
    .map(subfieldColor), [scholars])
  const scanCols = Math.max(1, Math.ceil(scanDots.length / SCAN_ROWS))

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

  async function submit() {
    const q = query.trim()
    if (q.length < 3 || running) return
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    onResults(null)
    setOutcome(null)
    setNow(Date.now())
    setPhase({
      kind: 'running', startedAt: Date.now(), queuePosition: 0, engine: null,
      seed: Math.floor(Math.random() * SPINNER_VERBS.length),
    })
    window.goatcounter?.count({ path: 'ai-search', title: 'AI search', event: true })
    try {
      const { results: found, ...meta } = await runAskSearch(
        q,
        (p) => setPhase((prev) => prev.kind === 'running'
          ? { ...prev, queuePosition: p.status === 'queued' ? p.queuePosition + 1 : 0, engine: p.engine }
          : prev),
        controller.signal,
      )
      onResults(found)
      setOutcome(meta)
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
              Describe a topic or method, or paste an abstract to find reviewers.{' '}
              {scholars.length ? `All ${scholars.length} PI profiles are read` : 'Every PI profile is read'} and the ten
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
                <li key={ex.label}>
                  <button type="button" onClick={() => fill(ex.text)}>{ex.label}</button>
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
            {scanDots.length > 0 && (
              <div className={cx('ask-scan', phase.queuePosition > 0 && 'is-waiting')}>
                <p className="ask-scan__head">
                  <span className="ask-scan__count">{scanDots.length.toLocaleString()}</span>
                  <span className="ask-scan__unit">PI profiles in the search</span>
                </p>
                <div
                  className="ask-scan__field"
                  aria-hidden="true"
                  style={{ gridTemplateRows: `repeat(${SCAN_ROWS}, auto)`, gridTemplateColumns: `repeat(${scanCols}, 1fr)` }}
                >
                  {scanDots.map((color, i) => (
                    <span
                      key={i}
                      style={{
                        backgroundColor: color,
                        animationDelay: `${(Math.floor(i / SCAN_ROWS) / scanCols - 1) * SCAN_PERIOD_S}s`,
                      }}
                    />
                  ))}
                </div>
              </div>
            )}
            {phase.engine && (
              <p className="ask__note">
                {ENGINE_LABELS[phase.engine]} is reading every profile.{' '}
                {phase.engine === 'claude' ? 'Usually 20–30 seconds.' : 'Usually about a minute.'}
              </p>
            )}
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
              <button type="button" className="ask__link" onClick={() => { onResults(null); setOutcome(null); fill('') }}>
                Clear
              </button>
            </div>
            {outcome?.engine && (
              <p className="ask__meta">
                {outcome.cached && 'Saved result · '}
                {ENGINE_LABELS[outcome.engine]}
                {outcome.seconds != null && ` · ${Math.round(outcome.seconds)} s`}
                {outcome.costUsd != null && ` · $${outcome.costUsd.toFixed(2)} API cost`}
              </p>
            )}
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
