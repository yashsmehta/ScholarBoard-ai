import { useEffect, useMemo, useState } from 'react'
import type { ResearchIdea, Scholar } from '../types/scholar'
import { clusterColor } from '../map/colorScale'
import { DEFAULT_AVATAR_URL, scholarAvatarUrl } from '../lib/scholarMedia'
import { cx } from '../lib/cx'

type SidebarTab = 'profile' | 'idea'

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
  const [activeTab, setActiveTab] = useState<SidebarTab>('profile')
  const nearby = useMemo(
    () => (scholar ? findNearbyScholars(scholar, allScholars, 5) : []),
    [scholar?.id, allScholars],
  )

  // Reset to profile tab when a new scholar is selected
  useEffect(() => {
    setActiveTab('profile')
  }, [scholar?.id])

  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <p className="sidebar__eyebrow">Scholar Profile</p>
        <button type="button" className="sidebar__close icon-button" onClick={onClose} aria-label="Close sidebar">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <line x1="4" y1="4" x2="12" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="12" y1="4" x2="4" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>

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
          <div className="sidebar__tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'profile'}
              className={cx('sidebar__tab', activeTab === 'profile' && 'is-active')}
              onClick={() => setActiveTab('profile')}
            >
              Profile
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'idea'}
              className={cx('sidebar__tab', activeTab === 'idea' && 'is-active')}
              onClick={() => setActiveTab('idea')}
            >
              Research Idea
            </button>
          </div>

          <div className="sidebar__content">
            {activeTab === 'profile' && (
              <ProfileTab scholar={scholar} nearby={nearby} onSelectNearby={onSelectNearby} onSubfieldClick={onSubfieldClick} />
            )}
            {activeTab === 'idea' && (
              <IdeaTab idea={scholar.suggestedIdea} scholarName={scholar.name} />
            )}
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
  return (
    <>
      <section className="profile-card">
        <div className="profile-card__meta">
          <ScholarAvatar scholar={scholar} />
          <div>
            <h3>{scholar.name}</h3>
            <p>{scholar.institution ?? 'Unknown institution'}</p>
            {scholar.department && <p className="muted">{scholar.department}</p>}
            {scholar.labUrl && (
              <a href={scholar.labUrl} target="_blank" rel="noreferrer" className="profile-card__lab-link">
                {scholar.labName ?? 'Lab website'}
              </a>
            )}
          </div>
        </div>
        {scholar.bio && <p className="profile-card__bio">{scholar.bio}</p>}
      </section>

      {scholar.subfields.length > 0 && (
        <section className="sidebar-section">
          <h3>Research Subfields</h3>
          <div className="tag-list">
            {scholar.subfields.map((sf) => (
              <button
                key={sf.subfield}
                type="button"
                className={cx(
                  'subfield-badge',
                  sf.subfield === scholar.primarySubfield && 'subfield-badge--primary',
                )}
                onClick={() => onSubfieldClick?.(sf.subfield)}
                title={`Filter by ${sf.subfield}`}
              >
                {sf.subfield}
              </button>
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
    </>
  )
}

function IdeaTab({ idea, scholarName }: { idea?: ResearchIdea; scholarName: string }) {
  if (!idea) {
    return (
      <div className="sidebar__empty">
        <svg className="sidebar__empty-icon" width="40" height="40" viewBox="0 0 40 40" fill="none" aria-hidden="true">
          <circle cx="20" cy="20" r="14" stroke="currentColor" strokeWidth="1.5" />
          <path d="M20 12v8M16 24h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <p>No AI-generated research idea available for {scholarName} yet.</p>
      </div>
    )
  }

  return (
    <>
      <section className="idea-card">
        <h3 className="idea-card__title">{idea.title}</h3>
        {idea.researchThread && (
          <p className="idea-card__thread">{idea.researchThread}</p>
        )}
      </section>

      <section className="sidebar-section">
        <h3>Open Question</h3>
        <p className="idea-section__text">{idea.openQuestion}</p>
      </section>

      <section className="sidebar-section">
        <h3>Hypothesis</h3>
        <p className="idea-section__text">{idea.hypothesis}</p>
      </section>

      <section className="sidebar-section">
        <h3>Approach</h3>
        <p className="idea-section__text">{idea.approach}</p>
      </section>

      <section className="sidebar-section">
        <h3>Scientific Impact</h3>
        <p className="idea-section__text">{idea.scientificImpact}</p>
      </section>

      {idea.whyNow && (
        <section className="sidebar-section">
          <h3>Why Now</h3>
          <p className="idea-section__text">{idea.whyNow}</p>
        </section>
      )}
    </>
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
