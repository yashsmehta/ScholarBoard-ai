import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { Header } from './components/Header'
import { Onboarding } from './components/Onboarding'
import { MethodologyModal } from './components/MethodologyModal'
import { FieldDirectionsPage } from './components/FieldDirectionsPage'
import type { FieldDirectionsData } from './components/FieldDirectionsPage'
import { SearchPanel } from './components/SearchPanel'
import { FilterPanel } from './components/FilterPanel'
import { MapControls } from './components/MapControls'
import { Sidebar } from './components/Sidebar'
import { ScholarMap } from './components/ScholarMap'
import { ScholarList } from './components/ScholarList'
import { BetaBanner } from './components/BetaBanner'
import { loadScholars } from './lib/loadScholars'
import { detectFrontendMode } from './lib/appMode'
import { appReducer, initialAppState } from './state/appReducer'
import { cx } from './lib/cx'
import type { Scholar } from './types/scholar'

function App() {
  const mode = detectFrontendMode()
  const [state, dispatch] = useReducer(appReducer, initialAppState)
  const [showOnboarding, setShowOnboarding] = useState(() => !localStorage.getItem('sb_onboarding_done'))
  const [showMethodology, setShowMethodology] = useState(false)
  const [showFieldDirections, setShowFieldDirections] = useState(false)
  const [fieldDirectionsData, setFieldDirectionsData] = useState<FieldDirectionsData | null>(null)

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

  const visibleScholars =
    state.activeInstitutions.length === 0
      ? state.scholars
      : state.scholars.filter((scholar) =>
          state.activeInstitutions.includes(scholar.institution ?? 'Unknown'),
        )

  // For list view, apply both institution and subfield filters
  // Sort primary subfield matches first when a subfield filter is active
  const filteredScholars = (() => {
    if (state.activeSubfields.length === 0) return visibleScholars
    const matching = visibleScholars.filter((scholar) => {
      const scholarSubfields = scholar.subfields.map((sf) => sf.subfield)
      if (state.subfieldFilterMode === 'intersection') {
        return state.activeSubfields.every((sf) => scholarSubfields.includes(sf))
      }
      return state.activeSubfields.some((sf) => scholarSubfields.includes(sf))
    })
    return matching.sort((a, b) => {
      const aPrimary = a.subfields[0]?.subfield
      const bPrimary = b.subfields[0]?.subfield
      const aIsPrimary = aPrimary != null && state.activeSubfields.includes(aPrimary)
      const bIsPrimary = bPrimary != null && state.activeSubfields.includes(bPrimary)
      if (aIsPrimary && !bIsPrimary) return -1
      if (!aIsPrimary && bIsPrimary) return 1
      return 0
    })
  })()

  const selectedScholar =
    state.selectedScholarId == null
      ? null
      : state.scholars.find((scholar) => scholar.id === state.selectedScholarId) ?? null

  const institutions = buildCounts(state.scholars, (s) => [s.institution ?? 'Unknown'])
  const subfields = buildCounts(state.scholars, (s) => s.subfields.map((sf) => sf.subfield))
  // Ref to suppress pushState when handling popstate (back/forward button)
  const isPopStateRef = useRef(false)

  const selectScholar = useCallback(
    (scholarId: string, options?: { pan?: boolean }) => {
      dispatch({ type: 'scholar_selected', scholarId })
      if (options?.pan) {
        dispatch({ type: 'pan_to_scholar_requested', scholarId })
      }
      if (!isPopStateRef.current) {
        history.pushState({ scholarId }, '')
      }
    },
    [],
  )

  const closeSidebar = useCallback(() => {
    dispatch({ type: 'sidebar_closed' })
    if (!isPopStateRef.current) {
      history.pushState({ scholarId: null }, '')
    }
  }, [])

  // Handle browser back/forward navigation
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      isPopStateRef.current = true
      const scholarId = event.state?.scholarId ?? null
      if (scholarId) {
        selectScholar(scholarId, { pan: true })
      } else {
        dispatch({ type: 'sidebar_closed' })
      }
      isPopStateRef.current = false
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [selectScholar])

  return (
    <div className="app-shell">
      <Header
        modeLabel={mode === 'embedded' ? 'Embedded' : undefined}
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
      <main className="app-main">
        <section className={cx('map-panel', state.viewMode === 'list' && 'map-panel--list')} aria-label="Scholar map panel">
          <div className="map-overlay map-overlay-left">
            <SearchPanel
              scholars={visibleScholars}
              query={state.searchQuery}
              selectedScholarId={state.selectedScholarId}
              onQueryChange={(query) => dispatch({ type: 'search_query_changed', query })}
              onSelectScholar={(scholar) => selectScholar(scholar.id, { pan: true })}
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
              <button
                className="view-toggle icon-button"
                onClick={() => dispatch({ type: 'view_mode_toggled' })}
                aria-label={state.viewMode === 'map' ? 'Switch to list view' : 'Switch to map view'}
                title={state.viewMode === 'map' ? 'List view' : 'Map view'}
              >
                {state.viewMode === 'map' ? (
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true">
                    <rect x="1" y="1" width="6" height="6" rx="1" />
                    <rect x="9" y="1" width="6" height="6" rx="1" />
                    <rect x="1" y="9" width="6" height="6" rx="1" />
                    <rect x="9" y="9" width="6" height="6" rx="1" />
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                    <circle cx="4" cy="4" r="1.5" />
                    <circle cx="10" cy="3" r="1.5" />
                    <circle cx="7" cy="8" r="1.5" />
                    <circle cx="12" cy="7" r="1.5" />
                    <circle cx="3" cy="11" r="1.5" />
                    <circle cx="9" cy="12" r="1.5" />
                    <circle cx="14" cy="11" r="1.5" />
                  </svg>
                )}
                {state.viewMode === 'map' ? 'List' : 'Map'}
              </button>
            </div>
          </div>

          {state.viewMode === 'map' ? (
            <ScholarMap
              scholars={state.scholars}
              activeInstitutions={state.activeInstitutions}
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
