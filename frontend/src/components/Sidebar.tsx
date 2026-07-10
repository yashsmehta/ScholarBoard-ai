import React, { useEffect, useMemo, useState } from 'react'
import type { Scholar } from '../types/scholar'
import { subfieldColor } from '../map/colorScale'
import { DEFAULT_AVATAR_URL, scholarAvatarUrl } from '../lib/scholarMedia'
import { cx } from '../lib/cx'

interface SidebarProps {
  scholar: Scholar | null
  allScholars: Scholar[]
  onClose: () => void
  onSelectNearby: (scholarId: string) => void
  onSubfieldClick?: (subfield: string) => void
}

interface NearbyScholar {
  scholar: Scholar
  distance: number
}

export function Sidebar({ scholar, allScholars, onClose, onSelectNearby, onSubfieldClick }: SidebarProps) {
  const [expanded, setExpanded] = useState(false)
  const touchStartY = React.useRef<number | null>(null)
  const nearby = useMemo(
    () => (scholar ? findNearbyScholars(scholar, allScholars, 5) : []),
    [scholar?.id, allScholars],
  )

  // Collapse when a new scholar is selected
  useEffect(() => {
    setExpanded(false)
  }, [scholar?.id])

  const handleClose = () => {
    setExpanded(false)
    onClose()
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartY.current = e.touches[0].clientY
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartY.current === null) return
    const deltaY = e.changedTouches[0].clientY - touchStartY.current
    if (deltaY < -30) setExpanded(true)
    else if (deltaY > 30) setExpanded(false)
    touchStartY.current = null
  }

  return (
    <aside className={cx('sidebar', expanded && scholar && 'sidebar--expanded')}>
      {!scholar && (
        <div className="sidebar__empty">
          <svg className="sidebar__empty-icon" width="40" height="40" viewBox="0 0 40 40" fill="none" aria-hidden="true">
            <circle cx="20" cy="14" r="6" stroke="currentColor" strokeWidth="1.5" />
            <path d="M8 34c0-6.627 5.373-12 12-12s12 5.373 12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <p>Select a scholar to explore their profile</p>
        </div>
      )}

      {scholar && (
        <>
          <div
            className="sidebar__handle"
            onClick={() => setExpanded(!expanded)}
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
          >
            <span className="sidebar__handle-pill" />
            <svg
              className={cx('sidebar__handle-chevron', expanded && 'is-flipped')}
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              aria-hidden="true"
            >
              <path d="M3 7.5l3-3 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>

          <div className="sidebar__header">
            <button type="button" className="sidebar__close" onClick={handleClose} aria-label="Close sidebar">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <line x1="4" y1="4" x2="12" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                <line x1="12" y1="4" x2="4" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
          </div>

          <div className="sidebar__content">
            <ProfileTab scholar={scholar} nearby={nearby} onSelectNearby={onSelectNearby} onSubfieldClick={onSubfieldClick} />
          </div>
        </>
      )}
    </aside>
  )
}

function ProfileTab({
  scholar,
  nearby,
  onSelectNearby,
  onSubfieldClick,
}: {
  scholar: Scholar
  nearby: NearbyScholar[]
  onSelectNearby: (scholarId: string) => void
  onSubfieldClick?: (subfield: string) => void
}) {
  const researchSummary = splitOpeningSentence(scholar.researchDirection)

  return (
    <>
      <section className="profile-card">
        <div className="profile-card__header">
          <ScholarAvatar scholar={scholar} />
          <div className="profile-card__info">
            <h3>{scholar.name}</h3>
            <p>{scholar.institution ?? 'Unknown institution'}</p>
            {scholar.department && <p className="muted">{scholar.department}</p>}
            {scholar.labUrl && (
              <a href={scholar.labUrl} target="_blank" rel="noreferrer" className="profile-card__lab-link">
                {scholar.labName ?? 'Lab website'}
              </a>
            )}
          </div>
          {(scholar.totalCitations != null || scholar.hIndex != null) && (
            <div className="profile-card__stats">
              {scholar.hIndex != null && (
                <div className="profile-stat">
                  <span className="profile-stat__value">{scholar.hIndex}</span>
                  <span className="profile-stat__label">H-Index</span>
                </div>
              )}
              {scholar.totalCitations != null && (
                <div className="profile-stat">
                  <span className="profile-stat__value">{scholar.totalCitations.toLocaleString()}</span>
                  <span className="profile-stat__label">Citations</span>
                </div>
              )}
            </div>
          )}
        </div>
        {scholar.subfields.length > 0 && (
          <div className="tag-list profile-card__tags">
            {scholar.subfields.map((sf) => {
              const isPrimary = sf.subfield === scholar.primarySubfield
              const color = subfieldColor(sf.subfield)
              return (
                <button
                  key={sf.subfield}
                  type="button"
                  className={cx('subfield-badge', isPrimary && 'subfield-badge--primary')}
                  style={{ '--sf-color': color } as React.CSSProperties}
                  onClick={() => onSubfieldClick?.(sf.subfield)}
                  title={`Filter by ${sf.subfield}`}
                >
                  {sf.subfield}
                </button>
              )
            })}
          </div>
        )}
        {researchSummary && (
          <div className="profile-card__research-summary">
            <h4 className="research-summary__header">
              Recent research
            </h4>
            <p>
              <strong className="research-summary__opening">{researchSummary.opening}</strong>
              {researchSummary.remainder && (
                <span className="research-summary__remainder">{researchSummary.remainder}</span>
              )}
            </p>
          </div>
        )}
      </section>

      {scholar.papers.length > 0 && (
        <section className="sidebar-section">
          <h3>Recent Papers</h3>
          <div className="stack-list">
            {scholar.papers.slice(0, 5).map((paper, index) => (
              <article key={`${paper.title}-${index}`} className="stack-list__item">
                <h4>
                  {paper.url ? (
                    <a href={paper.url} target="_blank" rel="noreferrer">
                      {paper.title}
                    </a>
                  ) : (
                    paper.title
                  )}
                </h4>
                <p className="muted">
                  {[paper.year, paper.venue]
                    .filter(Boolean)
                    .join(' \u2022 ')}
                </p>
              </article>
            ))}
          </div>
        </section>
      )}

      {scholar.education.length > 0 && (
        <section className="sidebar-section">
          <h3>Education</h3>
          <div className="stack-list">
            {scholar.education.map((entry, index) => (
              <article key={`${entry.degree ?? 'degree'}-${index}`} className="stack-list__item">
                <h4>
                  {entry.degree ?? 'Degree'}
                  {entry.field ? ` in ${entry.field}` : ''}
                </h4>
                <p className="muted">
                  {[
                    entry.institution,
                    entry.year && `(${entry.year})`,
                    entry.advisor && `Advisor: ${entry.advisor}`,
                  ]
                    .filter(Boolean)
                    .join(' \u2022 ')}
                </p>
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="sidebar-section">
        <h3>Similar Researchers</h3>
        <div className="nearby-list">
          {nearby.map((item) => (
            <button
              key={item.scholar.id}
              type="button"
              className="nearby-list__item"
              onClick={() => onSelectNearby(item.scholar.id)}
            >
              <span
                className="nearby-list__dot"
                style={{ backgroundColor: subfieldColor(item.scholar.subfields[0]?.subfield) }}
                aria-hidden="true"
              />
              <span className="nearby-list__text">
                <strong>{item.scholar.name}</strong>
                <small>{item.scholar.institution ?? 'Unknown institution'}</small>
              </span>
            </button>
          ))}
        </div>
      </section>
    </>
  )
}

function ScholarAvatar({ scholar }: { scholar: Scholar }) {
  const [src, setSrc] = useState<string | null>(() => scholarAvatarUrl(scholar))

  useEffect(() => {
    setSrc(scholarAvatarUrl(scholar))
  }, [scholar.id, scholar.profilePic])

  if (!src) {
    return (
      <div className="profile-card__avatar" aria-hidden="true">
        {initials(scholar.name)}
      </div>
    )
  }

  return (
    <div className="profile-card__avatar is-image">
      <img
        src={src}
        alt={`${scholar.name} profile`}
        onError={() => setSrc(src === DEFAULT_AVATAR_URL ? null : DEFAULT_AVATAR_URL)}
      />
    </div>
  )
}

function splitOpeningSentence(text?: string): { opening: string; remainder: string } | null {
  if (!text) return null
  const protectedText = text.replace(
    /\b(?:Dr|Prof|Mr|Mrs|Ms)\./g,
    (honorific) => `${honorific.slice(0, -1)}\u0000`,
  )
  const match = protectedText.match(/^(.+?[.!?])(?:\s+|$)(.*)$/s)
  if (!match) return { opening: text, remainder: '' }
  return {
    opening: match[1].replaceAll('\u0000', '.'),
    remainder: match[2].replaceAll('\u0000', '.'),
  }
}

function findNearbyScholars(scholar: Scholar, scholars: Scholar[], count: number): NearbyScholar[] {
  return scholars
    .filter((item) => item.id !== scholar.id)
    .map((item) => ({
      scholar: item,
      distance: Math.hypot(item.x - scholar.x, item.y - scholar.y),
    }))
    .sort((a, b) => a.distance - b.distance)
    .slice(0, count)
}

function initials(name: string): string {
  return name.split(/\s+/, 2).map((p) => p[0]?.toUpperCase() ?? '').join('')
}
