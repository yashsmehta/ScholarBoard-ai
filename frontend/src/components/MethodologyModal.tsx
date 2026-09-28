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
          ScholarBoard is a neighborhood map of 793 active vision-science PIs. Coordinates encode
          similarity between text representations of recent work; color encodes an independently
          assigned VSS topic area. The axes and absolute global distances have no direct meaning.
        </p>

        <div className="method-steps">
          <div className="method-step">
            <div className="method-step__num">01</div>
            <div>
              <h3>Corpus construction and PI inclusion</h3>
              <p>
                We started from about 920 researchers: most from recent VSS records, plus others
                found by <code>gemini-3-flash-preview</code> searching the web across the 21 VSS
                topic areas. Duplicate names were merged, and the map keeps the 793 who are active,
                independent vision-science PIs.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">02</div>
            <div>
              <h3>Evidence retrieval and current-work synthesis</h3>
              <p>
                <code>gemini-3.8-flash</code> searched the web to build each PI's profile and find
                up to five recent papers (2023 onward, with the PI as first or last author).{' '}
                <code>gemini-3.1-pro-preview</code> then summarized those papers into the
                current-research synopsis shown in the profile. These summaries are AI-generated,
                not written or endorsed by the researcher.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">03</div>
            <div>
              <h3>Representation and embedding</h3>
              <p>
                Each PI's current-research synopsis and recent papers are combined into a single
                text and converted into a numerical embedding with <code>gemini-embedding-001</code>. PIs
                whose embeddings are close together are treated as doing similar research.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">04</div>
            <div>
              <h3>Two-dimensional projection</h3>
              <p>
                UMAP flattens the embeddings into the 2D map, keeping similar researchers near each
                other. It only sets positions; colors come from the topic assignment below, not from
                clustering the map. Read the map by local neighborhoods; the axes, the shapes of
                groups, and long distances are not meaningful.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">05</div>
            <div>
              <h3>VSS topic assignment</h3>
              <p>
                Separately, <code>gemini-3.8-flash</code> reads each PI's profile and papers and
                assigns one main VSS topic area plus up to two secondary ones. The main topic sets
                the dot color; the others appear as tags on the profile.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">06</div>
            <div>
              <h3>Quality control and limitations</h3>
              <p>
                We spot-checked and corrected the data with help from Claude Code, but profiles,
                papers, summaries, and topics can still be incomplete or wrong. The map is a
                snapshot and will change as it is updated.
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
