import { useEffect, useMemo, useState } from 'react'
import type { Scholar } from '../types/scholar'
import { subfieldColor } from '../map/colorScale'
import { scholarAvatarUrl, DEFAULT_AVATAR_URL } from '../lib/scholarMedia'
import { cx } from '../lib/cx'

interface ScholarListProps {
  scholars: Scholar[]
  selectedScholarId: string | null
  onSelectScholar: (scholarId: string) => void
  searchQuery?: string
}

function ListAvatar({ scholar }: { scholar: Scholar }) {
  const [src, setSrc] = useState<string | null>(() => scholarAvatarUrl(scholar))

  useEffect(() => {
    setSrc(scholarAvatarUrl(scholar))
  }, [scholar.id, scholar.profilePic])

  const initials = scholar.name
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  if (!src) {
    return (
      <div className="scholar-list__avatar" aria-hidden="true">
        {initials}
      </div>
    )
  }

  return (
    <div className="scholar-list__avatar is-image">
      <img
        src={src}
        alt=""
        loading="lazy"
        onError={() => setSrc(src === DEFAULT_AVATAR_URL ? null : DEFAULT_AVATAR_URL)}
      />
    </div>
  )
}

interface LetterGroup {
  letter: string
  scholars: Scholar[]
}

function groupByLetter(scholars: Scholar[]): LetterGroup[] {
  const map = new Map<string, Scholar[]>()
  for (const s of scholars) {
    // Normalize accented characters to their base letter (Á→A, Ö→O, etc.)
    const raw = (s.name[0] ?? '?').toUpperCase()
    const letter = raw.normalize('NFD').replace(/[\u0300-\u036f]/g, '') || raw
    let group = map.get(letter)
    if (!group) {
      group = []
      map.set(letter, group)
    }
    group.push(s)
  }
  return Array.from(map.entries()).map(([letter, scholars]) => ({ letter, scholars }))
}

export function ScholarList({ scholars, selectedScholarId, onSelectScholar, searchQuery = '' }: ScholarListProps) {
  const q = searchQuery.trim().toLowerCase()
  const sorted = useMemo(
    () => [...scholars].sort((a, b) => a.name.localeCompare(b.name)),
    [scholars],
  )
  const groups = useMemo(() => groupByLetter(sorted), [sorted])

  if (scholars.length === 0) {
    return (
      <div className="scholar-list">
        <div className="scholar-list__empty">
          {q ? `No scholars match "${searchQuery}"` : 'No scholars to display'}
        </div>
      </div>
    )
  }

  return (
    <div className="scholar-list">
      <div className="scholar-list__spacer" />
      {groups.map((group) => (
        <div key={group.letter}>
          <div className="scholar-list__letter">{group.letter}</div>
          <div className="scholar-list__group">
            {group.scholars.map((scholar) => {
              const primarySubfield = scholar.subfields[0]?.subfield
              const color = subfieldColor(primarySubfield)
              return (
                <button
                  key={scholar.id}
                  className={cx(
                    'scholar-list__row',
                    scholar.id === selectedScholarId && 'scholar-list__row--selected',
                  )}
                  onClick={() => onSelectScholar(scholar.id)}
                >
                  <ListAvatar scholar={scholar} />
                  <span className="scholar-list__name">{highlight(scholar.name, q)}</span>
                  {scholar.institution && (
                    <span className="scholar-list__institution">{highlight(scholar.institution, q)}</span>
                  )}
                  {primarySubfield && (
                    <span
                      className="scholar-list__subfield"
                      style={{ '--sf-color': color } as React.CSSProperties}
                    >
                      {primarySubfield}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

function highlight(text: string, query: string): React.ReactNode {
  if (!query) return text
  const words = query.split(/\s+/).filter(Boolean)
  if (words.length === 0) return text
  const pattern = words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')
  const regex = new RegExp(`(${pattern})`, 'gi')
  const parts = text.split(regex)
  if (parts.length === 1) return text
  return (
    <>
      {parts.map((part, i) =>
        regex.test(part) ? <mark key={i} className="scholar-list__highlight">{part}</mark> : part
      )}
    </>
  )
}
