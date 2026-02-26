import { useEffect, useState } from 'react'
import { useClickOutside } from '../hooks/useClickOutside'
import { cx } from '../lib/cx'

interface InstitutionCount {
  name: string
  count: number
}

interface SubfieldCount {
  name: string
  count: number
}

type FilterTab = 'institution' | 'subfield'

interface FilterPanelProps {
  institutions: InstitutionCount[]
  activeInstitutions: string[]
  onApply: (institutions: string[]) => void
  onClear: () => void
  subfields: SubfieldCount[]
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
  const [draftInstitutions, setDraftInstitutions] = useState<string[]>(activeInstitutions)
  const [draftSubfields, setDraftSubfields] = useState<string[]>(activeSubfields)
  const containerRef = useClickOutside<HTMLDivElement>(() => setOpen(false))

  useEffect(() => {
    if (!open) {
      setDraftInstitutions(activeInstitutions)
      setDraftSubfields(activeSubfields)
    }
  }, [activeInstitutions, activeSubfields, open])

  function toggleInstitution(name: string) {
    setDraftInstitutions((current) =>
      current.includes(name) ? current.filter((v) => v !== name) : [...current, name],
    )
  }

  function toggleSubfield(name: string) {
    setDraftSubfields((current) =>
      current.includes(name) ? current.filter((v) => v !== name) : [...current, name],
    )
  }

  function handleApply() {
    if (activeTab === 'institution') {
      onApply(draftInstitutions)
    } else {
      onSubfieldsApply(draftSubfields)
    }
    setOpen(false)
  }

  function handleClear() {
    if (activeTab === 'institution') {
      setDraftInstitutions([])
      onClear()
    } else {
      setDraftSubfields([])
      onSubfieldsClear()
    }
  }

  const totalActive = activeInstitutions.length + activeSubfields.length

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
            <>
              <div className="filter-panel__header">
                <p>{institutions.length} institutions</p>
              </div>
              <div className="filter-panel__options">
                {institutions.slice(0, 80).map((institution) => (
                  <label key={institution.name} className="filter-option">
                    <input
                      type="checkbox"
                      checked={draftInstitutions.includes(institution.name)}
                      onChange={() => toggleInstitution(institution.name)}
                    />
                    <span className="filter-option__name">{institution.name}</span>
                    <span className="filter-option__count">{institution.count}</span>
                  </label>
                ))}
              </div>
            </>
          )}

          {activeTab === 'subfield' && (
            <>
              <div className="filter-panel__header">
                <p>{subfields.length} subfields</p>
              </div>
              <div className="filter-panel__options">
                {subfields.map((sf) => (
                  <label key={sf.name} className="filter-option">
                    <input
                      type="checkbox"
                      checked={draftSubfields.includes(sf.name)}
                      onChange={() => toggleSubfield(sf.name)}
                    />
                    <span className="filter-option__name">{sf.name}</span>
                    <span className="filter-option__count">{sf.count}</span>
                  </label>
                ))}
              </div>
            </>
          )}

          <div className="filter-panel__actions">
            <button type="button" className="icon-button is-primary" onClick={handleApply}>
              Apply
            </button>
            <button type="button" className="icon-button" onClick={handleClear}>
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
