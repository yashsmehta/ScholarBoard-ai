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
          ScholarBoard is a neighborhood map of 797 active vision-science PIs. Coordinates encode
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
                topic areas. Duplicate names were merged, and the map keeps the 797 who are active,
                independent vision-science PIs. New PIs are now added one at a time by name.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">02</div>
            <div>
              <h3>Profile research agent</h3>
              <p>
                Each new PI's profile is built by an AI research agent (<code>claude-sonnet-5-5</code>{' '}
                running in Claude Code) that searches the web and queries OpenAlex, Crossref and Google
                Scholar, in a fixed sequence: (1) identify the right person from their Google Scholar
                profile and own website; (2) find their current affiliation and lab page, with their own
                site and current university pages taking precedence, so recent moves are caught;
                (3) download a headshot from an official page that names them and check it visually;
                (4) read total citations and h-index from Google Scholar; (5) list every paper since
                January 2023 on which they are first or last author, excluding meeting abstracts,
                errata and preprint duplicates of published papers; (6) choose the five most impactful
                recent works by weighing venue, citations relative to the paper's age, recency and
                centrality to their research; (7) read each abstract and write the bio and the
                current-research summary from those papers; (8) assign VSS topic areas; (9) check its own work. Every chosen paper is then verified again
                against OpenAlex and Crossref before it is saved. Profiles from the first release were
                built with <code>gemini-3.8-flash</code> and <code>gemini-3.1-pro-preview</code>, then
                re-checked by per-PI Claude Code research agents in September 2026. Summaries are
                AI-generated, not written or endorsed by the researcher, unless the researcher sent
                their own text.
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
                whose embeddings are close together are treated as doing similar research. The “Similar Researchers” list in each profile ranks other PIs by cosine similarity of these full embeddings, not by distance on the map.
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
                Separately from the map position, each PI is assigned one main VSS topic area plus up
                to two secondary ones, judged from their profile and papers (by the profile agent for
                new PIs; by <code>gemini-3.8-flash</code> for the first release). The main topic sets
                the dot color; the others appear as tags on the profile.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">06</div>
            <div>
              <h3>Agentic Search</h3>
              <p>
                Agentic Search answers free-text requests (a topic, a method, “researchers like X”, or
                reviewers for an abstract) with an AI agent that works through the directory in
                tiers. <code>gemini-3.8-flash</code> first condenses each PI's profile into up to ten
                specific keywords on what they study and how (phenomena, methods, species, paradigms). For each request, the agent (Gemini via
                Antigravity, or Claude via Claude Code) applies a hard filter only when the request
                restricts eligibility, such as by country or institution. It then reads every PI's line
                and shortlists plausible matches, opens their full research summaries and recent
                paper titles, and ranks the ten best fits, giving a short reason for each. It only
                reads the directory, through a few read-only tools, and does not search the web.
                Rankings are a language model's judgment from these public profiles, so they can
                miss people or misjudge fit.
              </p>
            </div>
          </div>

          <div className="method-step">
            <div className="method-step__num">07</div>
            <div>
              <h3>Quality control and limitations</h3>
              <p>
                We spot-checked and corrected the data with help from Claude Code, but profiles,
                papers, summaries, and topics can still be incomplete or wrong. When a researcher
                sends corrections, their version is treated as ground truth and is never overwritten
                by an AI step. The map is a snapshot and will change as it is updated.
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
            or discuss collaboration at <a href="mailto:yashsmehta95@gmail.com">yashsmehta95@gmail.com</a>.
          </p>
        </div>

      </div>
    </div>
  )
}
