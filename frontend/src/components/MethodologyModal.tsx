interface MethodologyModalProps {
  onClose: () => void
}

export function MethodologyModal({ onClose }: MethodologyModalProps) {
  return (
    <div className="method-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Methodology">
      <div className="method-panel" onClick={(e) => e.stopPropagation()}>
        <button className="method-close" onClick={onClose} aria-label="Close">✕</button>

        <h2 className="method-title">Methods and interpretation</h2>
        <p className="method-intro">
          ScholarBoard is a neighborhood map of 801 active vision-science PIs. Coordinates encode
          similarity between text representations of recent work; color encodes an independently
          assigned VSS topic area. The axes and absolute global distances have no direct meaning.
        </p>

        <div className="method-steps">
          <div className="method-step">
            <div className="method-step__num">01</div>
            <div>
              <h3>Corpus construction and PI inclusion</h3>
              <p>
                The candidate pool contains 920 deduplicated researchers: 709 derived from recent
                VSS records and 211 added by <code>gemini-3-flash-preview</code> with Google Search grounding across the
                21 VSS topic areas. Names were normalized and resolved by exact/fuzzy matching;
                Gemini adjudicated ambiguous matches and PI-status edge cases. The released map
                retains 801 researchers classified as active, independent PIs.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">02</div>
            <div>
              <h3>Evidence retrieval and current-work synthesis</h3>
              <p>
                <code>gemini-3-flash-preview</code> with grounded web search assembled structured
                profiles and recent publication evidence. <code>gemini-3.1-pro-preview</code> with
                reasoning enabled then distilled each PI's recent papers into the current-research
                synopsis shown in the profile. These are model-generated summaries of retrieved
                evidence, not text supplied or endorsed by the researcher.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">03</div>
            <div>
              <h3>Representation and embedding</h3>
              <p>
                Each embedding input concatenates the current-research synopsis with recent paper
                titles and abstracts. <code>gemini-embedding-001</code>, configured with{' '}
                <code>task_type=CLUSTERING</code>, maps that text to a 3,072-dimensional vector.
                Cosine geometry in this space defines research similarity for the map.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">04</div>
            <div>
              <h3>Two-dimensional projection</h3>
              <p>
                UMAP produces the displayed coordinates with <code>n_neighbors=15</code>,{' '}
                <code>min_dist=0.1</code>, <code>metric=cosine</code>, two output components, and{' '}
                <code>random_state=42</code>. UMAP is used only for placement: no HDBSCAN or other
                clustering algorithm defines groups or colors. Interpret local neighborhoods;
                avoid treating axes, cluster shapes, or long-range distances as quantitative.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">05</div>
            <div>
              <h3>VSS topic assignment</h3>
              <p>
                Independently of UMAP, <code>gemini-3-flash-preview</code> reads the profile,
                current-work synopsis, and papers and selects one primary plus up to two secondary
                labels from an enum-constrained set of 21 VSS topic areas. The primary assignment
                determines dot color; secondary assignments appear as profile tags. Topic labels
                are language-model classifications, not clusters inferred from the 2D projection.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">06</div>
            <div>
              <h3>Quality control and limitations</h3>
              <p>
                Final refinement used targeted source checks, consistency audits, and corrections
                with agentic tooling, including Claude Code. Coverage, publication retrieval,
                PI status, summaries, and topic assignments can still be incomplete or wrong.
                The map is a versioned snapshot and may move as evidence, models, or inclusion
                decisions change.
              </p>
            </div>
          </div>
        </div>

        <div className="method-about">
          <p>
            Created by{' '}
            <a href="https://yashsmehta.com/" target="_blank" rel="noopener noreferrer"><strong>Yash Mehta</strong></a>
            {' '}and{' '}
            <a href="https://bonnerlab.org/" target="_blank" rel="noopener noreferrer"><strong>Mick Bonner</strong></a>
            {' '}at the Department of Cognitive Science, Johns Hopkins University. Report errors
            or discuss collaboration at <a href="mailto:ymehta3@jhu.edu">ymehta3@jhu.edu</a>.
          </p>
        </div>

      </div>
    </div>
  )
}
