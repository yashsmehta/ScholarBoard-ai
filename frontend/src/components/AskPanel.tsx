import { useEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import type { Scholar } from '../types/scholar'
import type { AskEngine, AskOutcome, AskResult, AskSteps } from '../lib/nlSearch'
import { ENGINE_LABELS, runAskSearch } from '../lib/nlSearch'
import { SPINNER_VERBS } from '../lib/spinnerVerbs'
import { ListAvatar } from './ScholarList'
import { cx } from '../lib/cx'
import { AskScan } from './AskScan'
import type { AskRun } from './AskScan'

interface AskPanelProps {
  open: boolean
  scholars: Scholar[]
  results: AskResult[] | null
  selectedScholarId: string | null
  onResults: (results: AskResult[] | null) => void
  onRunningChange: (running: boolean) => void
  onSelectScholar: (scholarId: string) => void
}

const REVIEW_ABSTRACT = 'A powerful approach to understand the computations carried out by the visual cortex is to build models that predict neural responses to any arbitrary image. Deep neural networks (DNNs) have emerged as the leading predictive models, yet their underlying computations remain buried beneath millions of parameters. Here we challenge the need for models at this scale by seeking predictive and parsimonious DNN models of the primate visual cortex. We first built a highly predictive DNN model of neural responses in macaque visual area V4 by alternating data collection and model training in adaptive closed-loop experiments. We then compressed this large, black-box DNN model, which comprised 60 million parameters, to identify compact models with 5,000 times fewer parameters yet comparable accuracy. This dramatic compression enabled us to investigate the inner workings of the compact models. We discovered a salient computational motif: compact models share similar filters in early processing, but individual models then specialize their feature selectivity by ‘consolidating’ this shared high-dimensional representation in distinct ways. We examined this consolidation step in a dot-detecting model neuron, revealing a computational mechanism that leads to a testable circuit hypothesis for dot-selective V4 neurons. Beyond V4, we found strong model compression for macaque visual areas V1 and IT (inferior temporal cortex), revealing a general computational principle of the visual cortex. Overall, our work challenges the notion that large DNNs are necessary to predict individual neurons and establishes a modelling framework that balances prediction and parsimony.'

// label is what the list shows; text is what a click puts in the box.
const EXAMPLES = [
  { label: 'Who would be the best reviewers for this abstract?', tag: 'sample abstract', text: `Who would be the best reviewers for this abstract?\n\n${REVIEW_ABSTRACT}` },
  'Labs using layer-resolved 7T fMRI or laminar recordings to separate feedforward from feedback signals in early visual cortex',
  'Labs in the Northeastern U.S. recording intracranially (sEEG/ECoG) from patients during visual recognition tasks',
  'Who studies whether microsaccades and fixational drift actively shape what we see at the fovea?',
].map((ex) => (typeof ex === 'string' ? { label: ex, text: ex, tag: undefined } : ex))

const MOD_KEY = /Mac|iPhone|iPad/.test(navigator.userAgent) ? '⌘' : 'Ctrl'
// Claude Code's status-line sparkle cycle (same as aos-ai); the verb changes every VERB_SECONDS.
const STARS = ['·', '✻', '✽', '✶', '*']
const VERB_SECONDS = 8

type Phase =
  | { kind: 'idle' }
  | { kind: 'running'; startedAt: number; queuePosition: number; seed: number; engine: AskEngine | null; run: AskRun | null }
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
      kind: 'running', startedAt: Date.now(), queuePosition: 0, engine: null, run: null,
      seed: Math.floor(Math.random() * SPINNER_VERBS.length),
    })
    window.goatcounter?.count({ path: 'ai-search', title: 'AI search', event: true })
    try {
      const { results: found, ...meta } = await runAskSearch(
        q,
        (p) => setPhase((prev) => prev.kind === 'running'
          ? {
              ...prev,
              queuePosition: p.status === 'queued' ? p.queuePosition + 1 : 0,
              engine: p.engine,
              run: p.status === 'running' ? nextRun(prev.run, p.expectedSeconds, p.steps) : prev.run,
            }
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

  function fill(text: string) {
    setQuery(text)
    requestAnimationFrame(() => {
      const el = textareaRef.current
      if (!el) return
      el.focus()
      el.setSelectionRange(text.length, text.length)
    })
  }

  const elapsedMs = phase.kind === 'running' ? Math.max(0, now - phase.startedAt) : 0
  const elapsed = Math.floor(elapsedMs / 1000)
  const star = STARS[Math.floor(elapsedMs / 260) % STARS.length]
  const verb = running
    ? SPINNER_VERBS[(phase.seed + Math.floor(elapsed / VERB_SECONDS) * 37) % SPINNER_VERBS.length] : ''
  const queuePosition = phase.kind === 'running' ? phase.queuePosition : 0

  return (
    <section className={cx('ask', !open && 'ask--hidden')} id="ws-panel-ai" role="tabpanel" aria-labelledby="ws-tab-ai" hidden={!open}>
      <div className="ask__inner">
        <header className="ask__head">
          <div>
            <h2 className="ask__title">Find researchers by what they study</h2>
            <p className="ask__lede">
              An agent reads every PI profile and ranks the ten closest matches, each with a reason.
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
          <div className="ask__composer">
            <textarea
              ref={textareaRef}
              className="ask__input"
              value={query}
              rows={query.length > 160 ? 8 : query.length > 70 ? 3 : 2}
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
              <span className="ask__hint">A topic, a method, or a whole abstract</span>
              {/* No cancel: the server keeps running a search once started, so a second one would be refused */}
              <button type="submit" className="ask__button" disabled={running || query.trim().length < 3}>
                {running ? 'Searching…' : 'Search'}
                {!running && <kbd className="ask__kbd" aria-hidden="true">{MOD_KEY}↵</kbd>}
              </button>
            </div>
          </div>
        </form>

        {phase.kind === 'idle' && results == null && (
          <div className="ask__examples">
            <p className="ask__label">For example</p>
            <ul>
              {EXAMPLES.map((ex) => (
                <li key={ex.label}>
                  <button type="button" onClick={() => fill(ex.text)}>
                    <span>
                      {ex.label}
                      {ex.tag && <span className="ask__tag">+ {ex.tag}</span>}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {running && (
          <div className="ask__status" role="status" aria-live="polite">
            <AskScan
              scholars={scholars}
              engine={phase.engine}
              waiting={queuePosition > 0}
              run={phase.run}
              now={now}
              status={(
                <>
                  <span className="ask__star" aria-hidden="true">{star}</span>
                  {queuePosition > 0 ? `Waiting for a free slot (#${queuePosition})` : `${verb}…`}
                  <span className="ask__time">{elapsed}s</span>
                </>
              )}
            />
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
              <div>
                <p className="ask__label">{results.length ? (
                    <>
                      {results.length} matches from {scholars.length.toLocaleString()} <span className="ask__keepcase">PIs</span>,
                      best first
                    </>
                  ) : 'No close matches'}</p>
                {outcome?.engine && (
                  <p className="ask__meta">
                    {outcome.cached && 'Saved result · '}
                    via <b>{ENGINE_LABELS[outcome.engine]}</b>
                    {outcome.seconds != null && ` · ${Math.round(outcome.seconds)} s`}
                    {outcome.costUsd != null && ` · $${outcome.costUsd.toFixed(2)} API cost`}
                  </p>
                )}
              </div>
              <button type="button" className="ask__clear" onClick={() => { onResults(null); setOutcome(null); fill('') }}>
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
                  <li key={r.id} style={{ '--i': i } as CSSProperties}>
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

/** Running-search state: when the run started (client clock) and when each step was first seen. */
function nextRun(prev: AskRun | null, expectedSeconds: number | null, steps: AskSteps | null): AskRun {
  const now = Date.now()
  const run = prev ?? { startedAt: now, expectedSeconds, steps: null, filteredAt: null, shortlistAt: null }
  return {
    ...run,
    expectedSeconds: expectedSeconds ?? run.expectedSeconds,
    steps: steps ?? run.steps,
    filteredAt: run.filteredAt ?? (steps?.filtered ? now : null),
    shortlistAt: run.shortlistAt ?? (steps?.shortlist != null ? now : null),
  }
}
