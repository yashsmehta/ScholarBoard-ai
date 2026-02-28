import { useState } from 'react'

export function BetaBanner() {
  const [dismissed, setDismissed] = useState(false)

  if (dismissed) return null

  return (
    <div className="map-overlay map-overlay-beta">
      <div className="beta-banner">
        <span className="beta-pill">BETA</span>
        <span className="beta-text">
          Reach out to{' '}
          <a href="mailto:ymehta3@jhu.edu">Yash Mehta</a>{' '}
          <span className="beta-email">(ymehta3@jhu.edu)</span>{' '}
          for feedback &amp; collaborations
        </span>
        <button
          className="beta-close"
          onClick={() => setDismissed(true)}
          aria-label="Close"
        >
          &times;
        </button>
      </div>
    </div>
  )
}
