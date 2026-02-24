import { useEffect, useState } from 'react'
import type { Scholar } from '../types/scholar'
import { clusterColor } from '../map/colorScale'
import { DEFAULT_AVATAR_URL, scholarAvatarUrl } from '../lib/scholarMedia'

interface SidebarProps {
  scholar: Scholar | null
  allScholars: Scholar[]
  onClose: () => void
  onSelectNearby: (scholarId: string) => void
}

interface NearbyScholar {
  scholar: Scholar
  distance: number
}

export function Sidebar({ scholar, allScholars, onClose, onSelectNearby }: SidebarProps) {
  const nearby = scholar ? findNearbyScholars(scholar, allScholars, 5) : []

  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <div>
          <p className="sidebar__eyebrow">Scholar Profile</p>
          <h2>{scholar?.name ?? 'No selection'}</h2>
        </div>
        <button type="button" className="icon-button" onClick={onClose}>
          Close
        </button>
      </div>

      {!scholar && (
        <div className="sidebar__empty">
          <p>Select a scholar to view their profile.</p>
          <small>Click any dot in the map or use search.</small>
        </div>
      )}

      {scholar && (
        <div className="sidebar__content">
          <section className="profile-card">
            <div className="profile-card__meta">
              <ScholarAvatar scholar={scholar} />
              <div>
                <h3>{scholar.name}</h3>
                <p>{scholar.institution ?? 'Unknown institution'}</p>
                {scholar.department && <p className="muted">{scholar.department}</p>}
              </div>
            </div>
            {scholar.bio && <p className="profile-card__bio">{scholar.bio}</p>}
          </section>

          {scholar.researchAreas.length > 0 && (
            <section className="sidebar-section">
              <h3>Research Areas</h3>
              <div className="tag-list">
                {scholar.researchAreas.map((area) => (
                  <span key={area} className="tag">
                    {area}
                  </span>
                ))}
              </div>
            </section>
          )}

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
                      {[paper.year, paper.venue, paper.citations && `${paper.citations} cit.`]
                        .filter(Boolean)
                        .join(' • ')}
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
                        .join(' • ')}
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
                    style={{ backgroundColor: clusterColor(item.scholar.cluster) }}
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
        </div>
      )}
    </aside>
  )
}

function ScholarAvatar({ scholar }: { scholar: Scholar }) {
  const [src, setSrc] = useState(() => scholarAvatarUrl(scholar))
  const [imageFailed, setImageFailed] = useState(false)

  useEffect(() => {
    setSrc(scholarAvatarUrl(scholar))
    setImageFailed(false)
  }, [scholar.id, scholar.profilePic])

  if (imageFailed) {
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
        onError={() => {
          if (src !== DEFAULT_AVATAR_URL) {
            setSrc(DEFAULT_AVATAR_URL)
            return
          }
          setImageFailed(true)
        }}
      />
    </div>
  )
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
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}
