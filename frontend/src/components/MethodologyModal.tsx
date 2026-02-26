interface MethodologyModalProps {
  onClose: () => void
}

export function MethodologyModal({ onClose }: MethodologyModalProps) {
  return (
    <div className="method-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Methodology">
      <div className="method-panel" onClick={(e) => e.stopPropagation()}>
        <button className="method-close" onClick={onClose} aria-label="Close">✕</button>

        <h2 className="method-title">How this map was made</h2>
        <p className="method-intro">
          ScholarBoard.ai arranges vision researchers on a 2D map so that researchers working on
          similar topics end up near each other — and those in different areas end up farther apart.
          Here is how it works.
        </p>

        <div className="method-steps">
          <div className="method-step">
            <div className="method-step__num">1</div>
            <div>
              <h3>The researchers</h3>
              <p>
                Researchers were drawn from two sources. The first is the Vision Sciences
                Society (VSS) — we started with roughly 730 presenters and attendees from
                recent VSS meetings. The second is an AI-powered search: for each of 23
                hand-curated vision neuroscience subfields (e.g., motion perception, scene
                understanding, visual cortex organization), we asked Gemini AI — with live
                web search — to find active researchers prominent in that area who weren't
                already in the VSS list. Both lists were merged and deduplicated, then
                filtered to principal investigators running their own research programs.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">2</div>
            <div>
              <h3>Finding recent work</h3>
              <p>
                For each researcher, we used Google's Gemini AI with live web search to collect
                recent publications. Rather than pulling from a static database, this approach
                captures current work and is not limited to papers with indexed abstracts.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">3</div>
            <div>
              <h3>Research fingerprints</h3>
              <p>
                The core challenge is quantifying research similarity. We used text embeddings:
                a neural network reads a researcher's papers and produces a list of ~3,000
                numbers — a compact fingerprint of their research. Two researchers working on
                similar problems will have similar fingerprints; those in unrelated areas will not.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">4</div>
            <div>
              <h3>Projecting onto the map</h3>
              <p>
                These high-dimensional fingerprints can't be plotted on a 2D screen directly.
                We used UMAP (Uniform Manifold Approximation and Projection) to compress each
                researcher's vector down to two coordinates — the x and y positions you see.
                UMAP preserves neighborhood structure: researchers who are similar in the full
                space will appear close together on the map.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">5</div>
            <div>
              <h3>Coloring by cluster</h3>
              <p>
                Each dot's color reflects a natural research cluster. We used HDBSCAN — a
                density-based clustering algorithm — to find groups of researchers who form
                coherent neighborhoods. Each color is a distinct cluster; grey dots are
                researchers who didn't fit cleanly into any group.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">6</div>
            <div>
              <h3>Subfield tags</h3>
              <p>
                Each researcher was tagged with one or more of 23 vision science subfields
                (e.g., Object Recognition, Eye Movements, fMRI/Neuroimaging). Tags were
                assigned by comparing each researcher's fingerprint to a description of each
                subfield and finding the closest matches.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">7</div>
            <div>
              <h3>AI research directions</h3>
              <p>
                For each PI, an AI-generated research idea is provided. The model is given the
                researcher's recent publications as context — their titles, abstracts, and
                findings — and asked to propose a novel direction that builds naturally on
                their existing work. These are generated by Gemini 3.1 Pro (High thinking
                mode) and are intended as conversation starters, not authoritative predictions.
              </p>
            </div>
          </div>
        </div>

        <div className="method-about">
          <h3>About</h3>
          <p>
            ScholarBoard.ai was created by <strong>Yash Mehta</strong>, from the laboratory
            of <strong>Michael F. (Mick) Bonner</strong> at the Department of Cognitive
            Science, Johns Hopkins University. The dataset covers researchers from the Vision
            Sciences Society (VSS) community.
          </p>
        </div>
      </div>
    </div>
  )
}
