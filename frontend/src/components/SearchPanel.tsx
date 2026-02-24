import { useDeferredValue, useEffect, useMemo, useRef, useState } from 'react'
import type { Scholar } from '../types/scholar'

interface SearchPanelProps {
  scholars: Scholar[]
  query: string
  selectedScholarId: string | null
  onQueryChange: (query: string) => void
  onSelectScholar: (scholar: Scholar) => void
}

const MIN_QUERY_LENGTH = 2
const MAX_RESULTS = 10

export function SearchPanel({
  scholars,
  query,
  selectedScholarId,
  onQueryChange,
  onSelectScholar,
}: SearchPanelProps) {
  const deferredQuery = useDeferredValue(query)
  const [isOpen, setIsOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const containerRef = useRef<HTMLDivElement | null>(null)

  const normalizedQuery = deferredQuery.trim().toLowerCase()
  const results = useMemo(() => {
    if (normalizedQuery.length < MIN_QUERY_LENGTH) return []
    return scholars
      .filter((scholar) => scholar.name.toLowerCase().includes(normalizedQuery))
      .slice(0, MAX_RESULTS)
  }, [scholars, normalizedQuery])

  useEffect(() => {
    if (results.length === 0) {
      setActiveIndex(-1)
      return
    }
    setActiveIndex(0)
    setIsOpen(true)
  }, [results])

  useEffect(() => {
    function handleDocumentClick(event: MouseEvent) {
      const target = event.target as Node | null
      if (!containerRef.current?.contains(target)) setIsOpen(false)
    }

    document.addEventListener('mousedown', handleDocumentClick)
    return () => document.removeEventListener('mousedown', handleDocumentClick)
  }, [])

  function selectScholar(scholar: Scholar) {
    onQueryChange(scholar.name)
    onSelectScholar(scholar)
    setIsOpen(false)
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (!isOpen || results.length === 0) return

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((index) => (index + 1) % results.length)
      return
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((index) => (index <= 0 ? results.length - 1 : index - 1))
      return
    }

    if (event.key === 'Enter') {
      event.preventDefault()
      const candidate = results[activeIndex >= 0 ? activeIndex : 0]
      if (candidate) selectScholar(candidate)
      return
    }

    if (event.key === 'Escape') {
      event.preventDefault()
      setIsOpen(false)
    }
  }

  return (
    <div className="search-panel" ref={containerRef}>
      <label className="search-panel__label" htmlFor="scholar-search">
        Search Scholars
      </label>
      <input
        id="scholar-search"
        className="search-panel__input"
        type="text"
        value={query}
        placeholder="Search by scholar name..."
        onChange={(event) => {
          onQueryChange(event.target.value)
          setIsOpen(true)
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={handleKeyDown}
      />
      <div className="search-panel__meta">
        {normalizedQuery.length < MIN_QUERY_LENGTH
          ? 'Type at least 2 letters'
          : `${results.length} result(s)`}
      </div>

      {isOpen && normalizedQuery.length >= MIN_QUERY_LENGTH && (
        <div className="search-results" role="listbox" aria-label="Scholar search results">
          {results.length === 0 && <div className="search-results__empty">No scholars found</div>}

          {results.map((scholar, index) => (
            <button
              key={scholar.id}
              type="button"
              role="option"
              aria-selected={selectedScholarId === scholar.id}
              className={[
                'search-results__item',
                index === activeIndex ? 'is-active' : '',
                selectedScholarId === scholar.id ? 'is-selected' : '',
              ]
                .filter(Boolean)
                .join(' ')}
              onMouseEnter={() => setActiveIndex(index)}
              onClick={() => selectScholar(scholar)}
            >
              <span className="search-results__title">{highlight(scholar.name, normalizedQuery)}</span>
              <span className="search-results__subtitle">
                {scholar.institution ?? 'Unknown institution'}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function highlight(text: string, query: string): React.ReactNode {
  if (!query) return text
  const lower = text.toLowerCase()
  const index = lower.indexOf(query)
  if (index < 0) return text
  return (
    <>
      {text.slice(0, index)}
      <mark>{text.slice(index, index + query.length)}</mark>
      {text.slice(index + query.length)}
    </>
  )
}
