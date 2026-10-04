import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { Header } from './components/Header'
import { Onboarding } from './components/Onboarding'
import { MethodologyModal } from './components/MethodologyModal'
import { FieldDirectionsPage } from './components/FieldDirectionsPage'
import type { FieldDirectionsData } from './components/FieldDirectionsPage'
import { SearchPanel } from './components/SearchPanel'
import { ViewToggle } from './components/ViewToggle'
import { FilterPanel } from './components/FilterPanel'
import { MapControls } from './components/MapControls'
import { Sidebar } from './components/Sidebar'
import { ScholarMap } from './components/ScholarMap'
import { ScholarList } from './components/ScholarList'
import { BetaBanner } from './components/BetaBanner'
import { AskPanel } from './components/AskPanel'
import { WorkspaceTabs, type WorkspaceTab } from './components/WorkspaceTabs'
import { NL_SEARCH_API, type AskResult } from './lib/nlSearch'
import { loadScholars } from './lib/loadScholars'
import { detectFrontendMode } from './lib/appMode'
import { appReducer, initialAppState } from './state/appReducer'
import { cx } from './lib/cx'
import type { Scholar } from './types/scholar'

function App() {
  const mode = detectFrontendMode()
  const [state, dispatch] = useReducer(appReducer, initialAppState)
  const [showOnboarding, setShowOnboarding] = useState(() => {
    if (new URLSearchParams(window.location.search).has('onboarding')) return true
    return !localStorage.getItem('sb_onboarding_done')
  })
  const [showMethodology, setShowMethodology] = useState(false)
  const [showFieldDirections, setShowFieldDirections] = useState(false)
  const [fieldDirectionsData, setFieldDirectionsData] = useState<FieldDirectionsData | null>(null)
  const [tab, setTab] = useState<WorkspaceTab>('directory')
  const askOpen = tab === 'ai'
  const [askResults, setAskResults] = useState<AskResult[] | null>(null)
  const [askRunning, setAskRunning] = useState(false)

  // The map is hidden while Agentic Search is open; once it is back (and resized), frame all dots.
  // Agentic Search results never change what the Directory shows.
  const wasAskOpenRef = useRef(false)
  useEffect(() => {
    if (wasAskOpenRef.current && !askOpen) {
      const frame = requestAnimationFrame(() => requestAnimationFrame(() => dispatch({ type: 'map_reset_requested' })))
      wasAskOpenRef.current = askOpen
      return () => cancelAnimationFrame(frame)
    }
    wasAskOpenRef.current = askOpen
  }, [askOpen])

  useEffect(() => {
    if (showFieldDirections && fieldDirectionsData == null) {
      fetch(`${import.meta.env.BASE_URL}data/build/field_directions.json`)
        .then((r) => r.json())
        .then((d: FieldDirectionsData) => setFieldDirectionsData(d))
        .catch(() => undefined)
    }
  }, [showFieldDirections, fieldDirectionsData])

  useEffect(() => {
    let cancelled = false

    async function run() {
      dispatch({ type: 'load_started' })
      try {
        const result = await loadScholars({ mode })
        if (cancelled) return
        dispatch({
          type: 'load_succeeded',
          scholars: result.scholars,
          sourceLabel: result.sourceLabel,
        })
      } catch (error) {
        if (cancelled) return
        const message = error instanceof Error ? error.message : 'Unknown error'
        dispatch({ type: 'load_failed', errorMessage: message })
      }
    }

    void run()

    return () => {
      cancelled = true
    }
  }, [mode])

  const visibleScholars = state.scholars.filter(
    (scholar) =>
      (state.activeInstitutions.length === 0 ||
        state.activeInstitutions.includes(scholar.institution ?? 'Unknown')) &&
      (state.activeCountries.length === 0 ||
        state.activeCountries.includes(scholar.country ?? 'Unknown')),
  )

  // Apply subfield filter on top of institution- and country-filtered scholars
  const subfieldFilteredScholars = (() => {
    if (state.activeSubfields.length === 0) return visibleScholars
    return visibleScholars.filter((scholar) => {
      const scholarSubfields = scholar.subfields.map((sf) => sf.subfield)
      if (state.subfieldFilterMode === 'intersection') {
        return state.activeSubfields.every((sf) => scholarSubfields.includes(sf))
      }
      return state.activeSubfields.some((sf) => scholarSubfields.includes(sf))
    })
  })()

  // For list view, apply live search query on top of all filters
  const filteredScholars = (() => {
    const q = state.searchQuery.trim().toLowerCase()
    if (state.viewMode === 'list' && q.length >= 1) {
      const words = q.split(/\s+/).filter(Boolean)
      return subfieldFilteredScholars.filter((scholar) => {
        const text = `${scholar.name} ${scholar.aliases.join(' ')} ${scholar.institution ?? ''}`.toLowerCase()
        return words.every((w) => text.includes(w))
      })
    }
    return subfieldFilteredScholars
  })()

  const selectedScholar =
    state.selectedScholarId == null
      ? null
      : state.scholars.find((scholar) => scholar.id === state.selectedScholarId) ?? null

  const institutions = buildCounts(state.scholars, (s) => [s.institution ?? 'Unknown'])
  const countries = buildCounts(state.scholars, (s) => [s.country ?? 'Unknown'])
  const subfields = buildCounts(state.scholars, (s) => s.subfields.map((sf) => sf.subfield))
  // Ref to suppress pushState when handling popstate (back/forward button)
  const isPopStateRef = useRef(false)

  const selectScholar = useCallback(
    (scholarId: string, options?: { pan?: boolean }) => {
      dispatch({ type: 'scholar_selected', scholarId })
      if (options?.pan) {
        dispatch({ type: 'pan_to_scholar_requested', scholarId })
      }
      if (!isPopStateRef.current && readScholarHash() !== scholarId) {
        history.pushState({ scholarId }, '', scholarUrl(scholarId))
      }
    },
    [],
  )

  const closeSidebar = useCallback(() => {
    dispatch({ type: 'sidebar_closed' })
    if (!isPopStateRef.current && readScholarHash() != null) {
      history.pushState({ scholarId: null }, '', scholarUrl(null))
    }
  }, [])

  // Deep link: open the scholar named in the URL hash once data has loaded
  const deepLinkHandledRef = useRef(false)
  useEffect(() => {
    if (state.status !== 'ready' || deepLinkHandledRef.current) return
    deepLinkHandledRef.current = true
    const id = readScholarHash()
    if (id == null || !state.scholars.some((s) => s.id === id)) return
    if (state.viewMode === 'list') dispatch({ type: 'view_mode_toggled' })
    isPopStateRef.current = true
    selectScholar(id, { pan: true })
    isPopStateRef.current = false
  }, [state.status, state.scholars, state.viewMode, selectScholar])

  // Handle browser back/forward navigation (the URL hash is the source of truth)
  useEffect(() => {
    const handlePopState = () => {
      isPopStateRef.current = true
      const scholarId = readScholarHash()
      if (scholarId) {
        selectScholar(scholarId, { pan: true })
      } else {
        dispatch({ type: 'sidebar_closed' })
      }
      isPopStateRef.current = false
    }
    window.addEventListener('popstate', handlePopState)
    window.addEventListener('hashchange', handlePopState)
    return () => {
      window.removeEventListener('popstate', handlePopState)
      window.removeEventListener('hashchange', handlePopState)
    }
  }, [selectScholar])

  return (
    <div className="app-shell">
      <Header
        modeLabel={mode === 'embedded' ? 'Embedded' : undefined}
        onLogoClick={() => {
          setTab('directory')
          if (state.viewMode === 'map') dispatch({ type: 'view_mode_toggled' })
          dispatch({ type: 'map_reset_requested' })
        }}
        onFieldDirectionsClick={() => setShowFieldDirections(true)}
        onMethodologyClick={() => setShowMethodology(true)}
        onTourClick={() => setShowOnboarding(true)}
      />
      {showOnboarding && state.status === 'ready' && (
        <Onboarding onComplete={() => {
          localStorage.setItem('sb_onboarding_done', '1')
          setShowOnboarding(false)
        }} />
      )}
      {showMethodology && <MethodologyModal onClose={() => setShowMethodology(false)} />}
      {showFieldDirections && (
        fieldDirectionsData != null ? (
          <FieldDirectionsPage data={fieldDirectionsData} onClose={() => setShowFieldDirections(false)} />
        ) : (
          <div className="fd-overlay" onClick={() => setShowFieldDirections(false)} role="dialog" aria-modal="true" aria-label="Loading">
            <div className="fd-panel fd-panel--loading" onClick={(e) => e.stopPropagation()}>
              <p className="fd-content__empty">Loading field directions…</p>
            </div>
          </div>
        )
      )}
      <main className={cx('app-main', !selectedScholar && 'app-main--empty')}>
        <div className={cx('workspace', `workspace--${askOpen ? 'ai' : state.viewMode}`, NL_SEARCH_API && 'workspace--tabbed')}>
        {NL_SEARCH_API && (
          <WorkspaceTabs
            active={tab}
            onChange={setTab}
            aiRunning={askRunning}
          />
        )}
        <div className="workspace__body">
        {NL_SEARCH_API && (
          <AskPanel
            open={askOpen}
            scholars={state.scholars}
            results={askResults}
            selectedScholarId={state.selectedScholarId}
            onResults={setAskResults}
            onRunningChange={setAskRunning}
            onSelectScholar={(scholarId) => selectScholar(scholarId)}
          />
        )}
        <section className={cx('map-panel', state.viewMode === 'list' && 'map-panel--list', askOpen && 'map-panel--hidden')} aria-label="Scholar map panel" id="ws-panel-directory" role={NL_SEARCH_API ? 'tabpanel' : undefined} aria-labelledby={NL_SEARCH_API ? 'ws-tab-directory' : undefined}>
          {state.viewMode === 'list' && <div className="map-panel__band" aria-hidden="true" />}
          <div className="map-overlay map-overlay-left">
            <SearchPanel
              scholars={subfieldFilteredScholars}
              query={state.searchQuery}
              selectedScholarId={state.selectedScholarId}
              onQueryChange={(query) => dispatch({ type: 'search_query_changed', query })}
              onSelectScholar={(scholar) => selectScholar(scholar.id, { pan: true })}
              hideDropdown={state.viewMode === 'list'}
            />
            <ViewToggle
              viewMode={state.viewMode}
              onChange={() => dispatch({ type: 'view_mode_toggled' })}
            />
          </div>

          <div className="map-overlay map-overlay-right">
            <div className="overlay-right-controls">
              <FilterPanel
                institutions={institutions}
                activeInstitutions={state.activeInstitutions}
                onApply={(institutionsToApply) =>
                  dispatch({ type: 'filters_applied', institutions: institutionsToApply })
                }
                onClear={() => dispatch({ type: 'filters_cleared' })}
                countries={countries}
                activeCountries={state.activeCountries}
                onCountriesApply={(countriesToApply) =>
                  dispatch({ type: 'countries_filter_applied', countries: countriesToApply })
                }
                onCountriesClear={() => dispatch({ type: 'countries_filter_cleared' })}
                subfields={subfields}
                activeSubfields={state.activeSubfields}
                subfieldFilterMode={state.subfieldFilterMode}
                onSubfieldsApply={(subfieldsToApply) =>
                  dispatch({ type: 'subfields_filter_applied', subfields: subfieldsToApply })
                }
                onSubfieldsClear={() => dispatch({ type: 'subfields_filter_cleared' })}
                onSubfieldFilterModeChange={(mode) =>
                  dispatch({ type: 'subfield_filter_mode_changed', mode })
                }
              />
            </div>
          </div>

          {state.viewMode === 'map' ? (
            <ScholarMap
              scholars={state.scholars}
              activeInstitutions={state.activeInstitutions}
              activeCountries={state.activeCountries}
              activeSubfields={state.activeSubfields}
              subfieldFilterMode={state.subfieldFilterMode}
              hoveredScholarId={state.hoveredScholarId}
              selectedScholarId={state.selectedScholarId}
              resetNonce={state.resetNonce}
              panRequest={state.panRequest}
              onHoverScholarId={(scholarId) => dispatch({ type: 'scholar_hovered', scholarId })}
              onSelectScholarId={(scholarId) => {
                if (scholarId == null) return
                selectScholar(scholarId)
              }}
            />
          ) : (
            <ScholarList
              scholars={filteredScholars}
              selectedScholarId={state.selectedScholarId}
              onSelectScholar={(scholarId) => selectScholar(scholarId)}
              searchQuery={state.searchQuery}
            />
          )}

          {state.viewMode === 'map' && (
            <MapControls
              onReset={() => dispatch({ type: 'map_reset_requested' })}
            />
          )}

          <BetaBanner />

          {state.status === 'error' && (
            <div className="overlay-error" role="alert">
              <h2>Unable to load scholars</h2>
              <p>{state.errorMessage}</p>
              <p className="overlay-error__hint">
                Start the data server (`python serve.py`) and use the Vite proxy, or set
                `VITE_SCHOLARS_URL`.
              </p>
            </div>
          )}
        </section>
        </div>
        </div>

        <Sidebar
          scholar={selectedScholar}
          allScholars={state.scholars}
          onClose={closeSidebar}
          onSelectNearby={(scholarId) => selectScholar(scholarId, { pan: true })}
          onSubfieldClick={(subfield) =>
            dispatch({ type: 'subfields_filter_applied', subfields: [subfield] })
          }
        />
      </main>
    </div>
  )
}

function readScholarHash(): string | null {
  const m = window.location.hash.match(/^#\/scholar\/(.+)$/)
  if (!m) return null
  try {
    return decodeURIComponent(m[1])
  } catch {
    return m[1]
  }
}

function scholarUrl(scholarId: string | null): string {
  const base = window.location.pathname + window.location.search
  return scholarId == null ? base : `${base}#/scholar/${encodeURIComponent(scholarId)}`
}

function buildCounts(
  scholars: Scholar[],
  getKeys: (scholar: Scholar) => string[],
): Array<{ name: string; count: number }> {
  const counts = new Map<string, number>()
  for (const scholar of scholars) {
    for (const key of getKeys(scholar)) {
      counts.set(key, (counts.get(key) ?? 0) + 1)
    }
  }
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
}

export default App
