import { useEffect, useMemo, useState } from 'react'
import type { Scholar } from '../types/scholar'
import { subfieldColor } from '../map/colorScale'
import { scholarAvatarUrl, DEFAULT_AVATAR_URL } from '../lib/scholarMedia'
import { cx } from '../lib/cx'

interface ScholarListProps {
  scholars: Scholar[]
  selectedScholarId: string | null
  onSelectScholar: (scholarId: string) => void
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
  const groups: LetterGroup[] = []
  let current: LetterGroup | null = null
  for (const s of scholars) {
    const letter = (s.name[0] ?? '?').toUpperCase()
    if (!current || current.letter !== letter) {
      current = { letter, scholars: [] }
      groups.push(current)
    }
    current.scholars.push(s)
  }
  return groups
}

export function ScholarList({ scholars, selectedScholarId, onSelectScholar }: ScholarListProps) {
  const groups = useMemo(() => groupByLetter(scholars), [scholars])

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
                  <span className="scholar-list__name">{scholar.name}</span>
                  {scholar.institution && (
                    <span className="scholar-list__institution">{scholar.institution}</span>
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
