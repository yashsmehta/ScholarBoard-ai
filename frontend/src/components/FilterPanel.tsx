import { useEffect, useRef, useState } from 'react'
import { useClickOutside } from '../hooks/useClickOutside'
import { subfieldColor } from '../map/colorScale'
import { cx } from '../lib/cx'

interface NameCount {
  name: string
  count: number
}

type FilterTab = 'institution' | 'subfield'

interface FilterPanelProps {
  institutions: NameCount[]
  activeInstitutions: string[]
  onApply: (institutions: string[]) => void
  onClear: () => void
  subfields: NameCount[]
  activeSubfields: string[]
  onSubfieldsApply: (subfields: string[]) => void
  onSubfieldsClear: () => void
}

export function FilterPanel({
  institutions,
  activeInstitutions,
  onApply,
  onClear,
  subfields,
  activeSubfields,
  onSubfieldsApply,
  onSubfieldsClear,
}: FilterPanelProps) {
  const [open, setOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<FilterTab>('institution')
  const [instSearch, setInstSearch] = useState('')
  const [draft, setDraft] = useState<Record<FilterTab, string[]>>({
    institution: activeInstitutions,
    subfield: activeSubfields,
  })
  const searchRef = useRef<HTMLInputElement>(null)
  const containerRef = useClickOutside<HTMLDivElement>(() => setOpen(false))

  useEffect(() => {
    if (!open) {
      setDraft({ institution: activeInstitutions, subfield: activeSubfields })
      setInstSearch('')
    }
  }, [activeInstitutions, activeSubfields, open])

  useEffect(() => {
    if (open && activeTab === 'institution') {
      setTimeout(() => searchRef.current?.focus(), 40)
    }
    if (activeTab !== 'institution') setInstSearch('')
  }, [open, activeTab])

  function toggleDraft(name: string) {
    setDraft((prev) => {
      const current = prev[activeTab]
      return {
        ...prev,
        [activeTab]: current.includes(name)
          ? current.filter((v) => v !== name)
          : [...current, name],
      }
    })
  }

  function handleApply() {
    if (activeTab === 'institution') {
      onApply(draft.institution)
    } else {
      onSubfieldsApply(draft.subfield)
    }
    setOpen(false)
  }

  function handleClear() {
    setDraft((prev) => ({ ...prev, [activeTab]: [] }))
    if (activeTab === 'institution') {
      onClear()
    } else {
      onSubfieldsClear()
    }
  }

  const totalActive = activeInstitutions.length + activeSubfields.length

  const knownInstitutions = institutions.filter((i) => !i.name.toLowerCase().includes('unknown'))
  const filteredInstitutions = instSearch.trim()
    ? knownInstitutions.filter((i) => i.name.toLowerCase().includes(instSearch.toLowerCase()))
    : knownInstitutions

  const items = activeTab === 'institution' ? filteredInstitutions : subfields

  return (
    <div className="filter-panel" ref={containerRef}>
      <button
        type="button"
        className={cx('icon-button', totalActive > 0 && 'is-emphasis')}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls="filter-menu"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <line x1="2" y1="4" x2="14" y2="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="4" y1="8" x2="12" y2="8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="6" y1="12" x2="10" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        Filters
        {totalActive > 0 && <span className="chip">{totalActive}</span>}
      </button>

      {open && (
        <div className="filter-panel__menu" id="filter-menu">
          <div className="filter-panel__tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'institution'}
              className={cx('filter-panel__tab', activeTab === 'institution' && 'is-active')}
              onClick={() => setActiveTab('institution')}
            >
              Institution
              {activeInstitutions.length > 0 && (
                <span className="filter-panel__tab-count">{activeInstitutions.length}</span>
              )}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'subfield'}
              className={cx('filter-panel__tab', activeTab === 'subfield' && 'is-active')}
              onClick={() => setActiveTab('subfield')}
            >
              Subfield
              {activeSubfields.length > 0 && (
                <span className="filter-panel__tab-count">{activeSubfields.length}</span>
              )}
            </button>
          </div>

          {activeTab === 'institution' && (
            <div className="filter-panel__search">
              <svg className="filter-panel__search-icon" width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" strokeWidth="1.5" />
                <line x1="10" y1="10" x2="14" y2="14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              <input
                ref={searchRef}
                type="text"
                className="filter-panel__search-input"
                placeholder="Search institutions…"
                value={instSearch}
                onChange={(e) => setInstSearch(e.target.value)}
              />
            </div>
          )}

          <div className="filter-panel__options">
            {items.length === 0 && (
              <p className="filter-panel__empty">No matches</p>
            )}
            {items.map((item) => (
              <label key={item.name} className="filter-option">
                <input
                  type="checkbox"
                  checked={draft[activeTab].includes(item.name)}
                  onChange={() => toggleDraft(item.name)}
                />
                <span className="filter-option__name">
                  {activeTab === 'subfield' && (
                    <span
                      className="filter-option__dot"
                      style={{ backgroundColor: subfieldColor(item.name) }}
                    />
                  )}
                  {item.name}
                </span>
                <span className="filter-option__count">{item.count}</span>
              </label>
            ))}
          </div>

          <div className="filter-panel__actions">
            <button type="button" className="filter-panel__apply" onClick={handleApply}>
              Apply
            </button>
            <button type="button" className="filter-panel__clear" onClick={handleClear}>
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
