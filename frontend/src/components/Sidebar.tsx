import React, { useEffect, useMemo, useState } from 'react'
import type { ResearchIdea, Scholar } from '../types/scholar'
import { subfieldColor } from '../map/colorScale'
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
            <button type="button" className="sidebar__close" onClick={onClose} aria-label="Close sidebar">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <line x1="4" y1="4" x2="12" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                <line x1="12" y1="4" x2="4" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
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
    <div className="idea-pane">
      <div className="idea-hero">
        <div className="idea-hero__badge">
          <svg width="11" height="11" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true">
            <path d="M6 0l1.2 3.6L11 4.8l-2.8 2.7.7 3.9L6 9.6l-2.9 1.8.7-3.9L1 4.8l3.8-1.2z"/>
          </svg>
          AI Research Idea
        </div>
        <h3 className="idea-hero__title">{idea.title}</h3>
        {idea.researchThread && (
          <p className="idea-hero__thread">{idea.researchThread}</p>
        )}
      </div>

      <div className="idea-blocks">
        {idea.openQuestion && (
          <div className="idea-block">
            <div className="idea-block__label">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" strokeWidth="1.3"/>
                <path d="M6.5 9v-.8M5 5.2a1.5 1.5 0 012.9.5c0 1-1.4 1.5-1.4 2.1" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              Open Question
            </div>
            <p className="idea-block__body">{idea.openQuestion}</p>
          </div>
        )}

        {idea.hypothesis && (
          <div className="idea-block">
            <div className="idea-block__label">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <path d="M6.5 1.5a3.5 3.5 0 011 6.84V9.5H5.5V8.34A3.5 3.5 0 016.5 1.5z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
                <path d="M5.5 11h3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              Hypothesis
            </div>
            <p className="idea-block__body">{idea.hypothesis}</p>
          </div>
        )}

        {idea.approach && (
          <div className="idea-block">
            <div className="idea-block__label">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <path d="M2 10.5l2.5-3 2 2 2.5-4 2 4.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
                <rect x="1.5" y="1.5" width="10" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.2"/>
              </svg>
              Approach
            </div>
            <p className="idea-block__body">{idea.approach}</p>
          </div>
        )}

        {idea.scientificImpact && (
          <div className="idea-block">
            <div className="idea-block__label">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <circle cx="6.5" cy="6.5" r="2" stroke="currentColor" strokeWidth="1.3"/>
                <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.2"/>
              </svg>
              Scientific Impact
            </div>
            <p className="idea-block__body">{idea.scientificImpact}</p>
          </div>
        )}

        {idea.whyNow && (
          <div className="idea-block">
            <div className="idea-block__label">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.2"/>
                <path d="M6.5 4v2.5l2 1.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              Why Now
            </div>
            <p className="idea-block__body">{idea.whyNow}</p>
          </div>
        )}
      </div>
    </div>
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
