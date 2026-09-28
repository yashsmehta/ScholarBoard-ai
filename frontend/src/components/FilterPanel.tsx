import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useClickOutside } from '../hooks/useClickOutside'
import { subfieldColor } from '../map/colorScale'
import { cx } from '../lib/cx'

interface NameCount {
  name: string
  count: number
}

type SubfieldFilterMode = 'union' | 'intersection'

interface FilterPanelProps {
  institutions: NameCount[]
  activeInstitutions: string[]
  onApply: (institutions: string[]) => void
  onClear: () => void
  countries: NameCount[]
  activeCountries: string[]
  onCountriesApply: (countries: string[]) => void
  onCountriesClear: () => void
  subfields: NameCount[]
  activeSubfields: string[]
  subfieldFilterMode: SubfieldFilterMode
  onSubfieldsApply: (subfields: string[]) => void
  onSubfieldsClear: () => void
  onSubfieldFilterModeChange: (mode: SubfieldFilterMode) => void
}

export function FilterPanel({
  institutions,
  activeInstitutions,
  onApply,
  onClear,
  countries,
  activeCountries,
  onCountriesApply,
  onCountriesClear,
  subfields,
  activeSubfields,
  subfieldFilterMode,
  onSubfieldsApply,
  onSubfieldsClear,
  onSubfieldFilterModeChange,
}: FilterPanelProps) {
  const knownInstitutions = institutions.filter((i) => !i.name.toLowerCase().includes('unknown'))

  return (
    <>
      <FilterDropdown
        id="institution-filter-menu"
        label="Institution"
        items={knownInstitutions}
        active={activeInstitutions}
        searchPlaceholder="Search institutions…"
        onApply={onApply}
        onClear={onClear}
      />
      <FilterDropdown
        id="country-filter-menu"
        label="Country"
        items={countries.filter((c) => c.name !== 'Unknown')}
        active={activeCountries}
        searchPlaceholder="Search countries…"
        onApply={onCountriesApply}
        onClear={onCountriesClear}
      />
      <FilterDropdown
        id="field-filter-menu"
        label="Field"
        items={subfields}
        active={activeSubfields}
        searchPlaceholder="Search fields…"
        showColorDots
        onApply={onSubfieldsApply}
        onClear={onSubfieldsClear}
        renderExtra={(selected) =>
          selected.length >= 2 && (
            <div className="filter-panel__mode-toggle">
              <span className="filter-panel__mode-label">Match</span>
              {(['union', 'intersection'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={cx('filter-panel__mode-btn', subfieldFilterMode === mode && 'is-active')}
                  onClick={() => onSubfieldFilterModeChange(mode)}
                  title={mode === 'union' ? 'Match any selected field' : 'Match all selected fields'}
                >
                  {mode === 'union' ? 'Any' : 'All'}
                </button>
              ))}
            </div>
          )
        }
      />
    </>
  )
}

interface FilterDropdownProps {
  id: string
  label: string
  items: NameCount[]
  active: string[]
  searchPlaceholder: string
  showColorDots?: boolean
  onApply: (values: string[]) => void
  onClear: () => void
  renderExtra?: (selected: string[]) => ReactNode
}

function FilterDropdown({
  id,
  label,
  items,
  active,
  searchPlaceholder,
  showColorDots = false,
  onApply,
  onClear,
  renderExtra,
}: FilterDropdownProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const searchRef = useRef<HTMLInputElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const containerRef = useClickOutside<HTMLDivElement>(() => setOpen(false))

  useEffect(() => {
    if (!open) return
    const timer = setTimeout(() => searchRef.current?.focus(), 40)
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.stopPropagation()
        setOpen(false)
        buttonRef.current?.focus()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      clearTimeout(timer)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open])

  function toggleOpen() {
    if (!open) setSearch('')
    setOpen(!open)
  }

  // Each tick applies immediately
  function toggleValue(name: string) {
    onApply(active.includes(name) ? active.filter((v) => v !== name) : [...active, name])
  }

  const query = search.trim().toLowerCase()
  const visibleItems = query ? items.filter((i) => i.name.toLowerCase().includes(query)) : items

  return (
    <div className="filter-panel" ref={containerRef}>
      <button
        ref={buttonRef}
        type="button"
        className={cx('icon-button', active.length > 0 && 'is-emphasis')}
        onClick={toggleOpen}
        aria-expanded={open}
        aria-controls={id}
        aria-haspopup="true"
      >
        {label}
        {active.length > 0 && <span className="chip">{active.length}</span>}
        <svg
          className={cx('filter-panel__caret', open && 'is-open')}
          width="10"
          height="10"
          viewBox="0 0 10 10"
          fill="none"
          aria-hidden="true"
        >
          <path d="M2 3.5 5 6.5 8 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <div className="filter-panel__menu" id={id} role="dialog" aria-label={`Filter by ${label.toLowerCase()}`}>
          <div className="filter-panel__search">
            <svg className="filter-panel__search-icon" width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" strokeWidth="1.5" />
              <line x1="10" y1="10" x2="14" y2="14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <input
              ref={searchRef}
              type="text"
              className="filter-panel__search-input"
              placeholder={searchPlaceholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="filter-panel__options">
            {visibleItems.length === 0 && <p className="filter-panel__empty">No matches</p>}
            {visibleItems.map((item) => (
              <label key={item.name} className="filter-option">
                <input
                  type="checkbox"
                  checked={active.includes(item.name)}
                  onChange={() => toggleValue(item.name)}
                />
                <span className="filter-option__name">
                  {showColorDots && (
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

          {renderExtra?.(active)}

          <div className="filter-panel__actions">
            <button
              type="button"
              className="filter-panel__clear"
              onClick={onClear}
              disabled={active.length === 0}
            >
              Clear
            </button>
            <button type="button" className="filter-panel__apply" onClick={() => setOpen(false)}>
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
