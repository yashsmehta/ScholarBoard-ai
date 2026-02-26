import { useEffect, useReducer, useState } from 'react'
import { Header } from './components/Header'
import { MethodologyModal } from './components/MethodologyModal'
import { SearchPanel } from './components/SearchPanel'
import { FilterPanel } from './components/FilterPanel'
import { MapControls } from './components/MapControls'
import { Sidebar } from './components/Sidebar'
import { ScholarMap } from './components/ScholarMap'
import { loadScholars } from './lib/loadScholars'
import { detectFrontendMode } from './lib/appMode'
import { appReducer, initialAppState } from './state/appReducer'
import type { Scholar } from './types/scholar'

function App() {
  const mode = detectFrontendMode()
  const [state, dispatch] = useReducer(appReducer, initialAppState)
  const [showMethodology, setShowMethodology] = useState(false)

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

  const selectedScholar =
    state.selectedScholarId == null
      ? null
      : state.scholars.find((scholar) => scholar.id === state.selectedScholarId) ?? null

  const institutions = buildCounts(state.scholars, (s) => [s.institution ?? 'Unknown'])
  const subfields = buildCounts(state.scholars, (s) => s.subfields.map((sf) => sf.subfield))
  const selectScholar = (scholarId: string, options?: { pan?: boolean }) => {
    dispatch({ type: 'scholar_selected', scholarId })
    if (options?.pan) {
      dispatch({ type: 'pan_to_scholar_requested', scholarId })
    }
  }

  return (
    <div className="app-shell">
      <Header
        modeLabel={mode === 'embedded' ? 'Embedded' : undefined}
        scholarCount={state.status === 'ready' ? state.scholars.length : undefined}
        onMethodologyClick={() => setShowMethodology(true)}
      />
      {showMethodology && <MethodologyModal onClose={() => setShowMethodology(false)} />}
      <main className="app-main">
        <section className="map-panel" aria-label="Scholar map panel">
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
            <FilterPanel
              institutions={institutions}
              activeInstitutions={state.activeInstitutions}
              onApply={(institutionsToApply) =>
                dispatch({ type: 'filters_applied', institutions: institutionsToApply })
              }
              onClear={() => dispatch({ type: 'filters_cleared' })}
              subfields={subfields}
              activeSubfields={state.activeSubfields}
              onSubfieldsApply={(subfieldsToApply) =>
                dispatch({ type: 'subfields_filter_applied', subfields: subfieldsToApply })
              }
              onSubfieldsClear={() => dispatch({ type: 'subfields_filter_cleared' })}
            />
          </div>

          <ScholarMap
            scholars={state.scholars}
            activeInstitutions={state.activeInstitutions}
            activeSubfields={state.activeSubfields}
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

          <MapControls
            onReset={() => dispatch({ type: 'map_reset_requested' })}
          />

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
          onClose={() => dispatch({ type: 'sidebar_closed' })}
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
