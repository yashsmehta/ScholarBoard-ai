import type { Scholar } from '../types/scholar'
import { subfieldColor } from '../map/colorScale'
import { cx } from '../lib/cx'

interface ScholarListProps {
  scholars: Scholar[]
  selectedScholarId: string | null
  onSelectScholar: (scholarId: string) => void
}

function ScholarAvatar({ scholar }: { scholar: Scholar }) {
  const initials = scholar.name
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  if (scholar.profilePic) {
    return (
      <div className="scholar-list__avatar is-image">
        <img
          src={`/images/profile_pics/${scholar.profilePic}`}
          alt=""
          loading="lazy"
          onError={(e) => {
            const el = e.currentTarget
            el.style.display = 'none'
            const parent = el.parentElement
            if (parent) {
              parent.classList.remove('is-image')
              parent.textContent = initials
            }
          }}
        />
      </div>
    )
  }

  return <div className="scholar-list__avatar">{initials}</div>
}

export function ScholarList({ scholars, selectedScholarId, onSelectScholar }: ScholarListProps) {
  return (
    <div className="scholar-list">
      <div className="scholar-list__grid">
        {scholars.map((scholar) => {
          const primarySubfield = scholar.subfields[0]?.subfield
          const color = subfieldColor(primarySubfield)
          return (
            <button
              key={scholar.id}
              className={cx(
                'scholar-list__card',
                scholar.id === selectedScholarId && 'scholar-list__card--selected',
              )}
              style={{ borderLeftColor: color }}
              onClick={() => onSelectScholar(scholar.id)}
            >
              <ScholarAvatar scholar={scholar} />
              <div className="scholar-list__info">
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
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
