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
          <a href="mailto:yashsmehta95@gmail.com">Yash Mehta</a>{' '}
          <span className="beta-email">(yashsmehta95@gmail.com)</span>{' '}
          for feedback
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
