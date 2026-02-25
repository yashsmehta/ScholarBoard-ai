import { useEffect, useRef, useState } from 'react'

interface InstitutionCount {
  name: string
  count: number
}

interface FilterPanelProps {
  institutions: InstitutionCount[]
  activeInstitutions: string[]
  onApply: (institutions: string[]) => void
  onClear: () => void
}

export function FilterPanel({
  institutions,
  activeInstitutions,
  onApply,
  onClear,
}: FilterPanelProps) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState<string[]>(activeInstitutions)
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) setDraft(activeInstitutions)
  }, [activeInstitutions, open])

  useEffect(() => {
    function onDocumentMouseDown(event: MouseEvent) {
      const target = event.target as Node | null
      if (!containerRef.current?.contains(target)) setOpen(false)
    }

    document.addEventListener('mousedown', onDocumentMouseDown)
    return () => document.removeEventListener('mousedown', onDocumentMouseDown)
  }, [])

  function toggleInstitution(name: string) {
    setDraft((current) =>
      current.includes(name) ? current.filter((value) => value !== name) : [...current, name],
    )
  }

  return (
    <div className="filter-panel" ref={containerRef}>
      <button
        type="button"
        className={['icon-button', activeInstitutions.length > 0 ? 'is-emphasis' : '']
          .filter(Boolean)
          .join(' ')}
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls="institution-filter-menu"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <line x1="2" y1="4" x2="14" y2="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="4" y1="8" x2="12" y2="8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="6" y1="12" x2="10" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        Filters
        {activeInstitutions.length > 0 && <span className="chip">{activeInstitutions.length}</span>}
      </button>

      {open && (
        <div className="filter-panel__menu" id="institution-filter-menu">
          <div className="filter-panel__header">
            <h2>Filter by Institution</h2>
            <p>{institutions.length} institutions</p>
          </div>
          <div className="filter-panel__options">
            {institutions.slice(0, 80).map((institution) => (
              <label key={institution.name} className="filter-option">
                <input
                  type="checkbox"
                  checked={draft.includes(institution.name)}
                  onChange={() => toggleInstitution(institution.name)}
                />
                <span className="filter-option__name">{institution.name}</span>
                <span className="filter-option__count">{institution.count}</span>
              </label>
            ))}
          </div>
          <div className="filter-panel__actions">
            <button
              type="button"
              className="icon-button is-primary"
              onClick={() => {
                onApply(draft)
                setOpen(false)
              }}
            >
              Apply
            </button>
            <button
              type="button"
              className="icon-button"
              onClick={() => {
                setDraft([])
                onClear()
              }}
            >
              Clear All
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
