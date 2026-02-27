import { useEffect, useRef, useState } from 'react'

interface FieldDirectionEntry {
  subfield: string
  n_researchers: number
  overview: string
  active_research_themes: Array<{ theme: string; description: string }>
  open_questions: string[]
  methods_and_approaches: Array<{ method: string; description: string }>
  emerging_directions: Array<{ direction: string; description: string }>
}

export type FieldDirectionsData = Record<string, FieldDirectionEntry>

interface FieldDirectionsPageProps {
  data: FieldDirectionsData
  onClose: () => void
}

export function FieldDirectionsPage({ data, onClose }: FieldDirectionsPageProps) {
  const subfields = Object.keys(data).sort()
  const [selected, setSelected] = useState<string>(subfields[0] ?? '')
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    contentRef.current?.scrollTo({ top: 0 })
  }, [selected])

  const entry = selected ? data[selected] : null

  return (
    <div className="fd-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Field Directions">
      <div className="fd-panel" onClick={(e) => e.stopPropagation()}>
        <button className="fd-close" onClick={onClose} aria-label="Close">✕</button>

        <div className="fd-nav">
          <div className="fd-nav__header">
            <h2 className="fd-nav__title">Field Directions</h2>
            <p className="fd-nav__subtitle">{subfields.length} research areas</p>
          </div>
          <ul className="fd-nav__list">
            {subfields.map((sf) => (
              <li key={sf}>
                <button
                  className={`fd-nav__item${selected === sf ? ' is-active' : ''}`}
                  onClick={() => setSelected(sf)}
                >
                  <span className="fd-nav__item-name">{sf}</span>
                  <span className="fd-nav__item-count">{data[sf].n_researchers}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="fd-content" ref={contentRef}>
          {entry ? (
            <>
              <div className="fd-content__header">
                <h2 className="fd-content__title">{entry.subfield}</h2>
                <span className="fd-content__meta">{entry.n_researchers} researchers</span>
              </div>

              <p className="fd-content__overview">{entry.overview}</p>

              <div className="fd-sections">
                <section>
                  <h3 className="fd-section__title">Active Research Themes</h3>
                  <div className="fd-themes">
                    {entry.active_research_themes.map((t, i) => (
                      <div key={i} className="fd-theme-card">
                        <h4 className="fd-theme-card__name">{t.theme}</h4>
                        <p className="fd-theme-card__desc">{t.description}</p>
                      </div>
                    ))}
                  </div>
                </section>

                <section>
                  <h3 className="fd-section__title">Open Questions</h3>
                  <ul className="fd-list">
                    {entry.open_questions.map((q, i) => (
                      <li key={i} className="fd-list__item">{q}</li>
                    ))}
                  </ul>
                </section>

                <div className="fd-two-col">
                  <section>
                    <h3 className="fd-section__title">Methods & Approaches</h3>
                    <div className="fd-methods">
                      {entry.methods_and_approaches.map((m, i) => (
                        <div key={i} className="fd-method-item">
                          <span className="fd-method-item__name">{m.method}</span>
                          <p className="fd-method-item__desc">{m.description}</p>
                        </div>
                      ))}
                    </div>
                  </section>

                  <section>
                    <h3 className="fd-section__title">Emerging Directions</h3>
                    <div className="fd-methods">
                      {entry.emerging_directions.map((d, i) => (
                        <div key={i} className="fd-method-item fd-method-item--emerging">
                          <span className="fd-method-item__name">{d.direction}</span>
                          <p className="fd-method-item__desc">{d.description}</p>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>
              </div>
            </>
          ) : (
            <p className="fd-content__empty">Select a field from the left panel.</p>
          )}
        </div>
      </div>
    </div>
  )
}
