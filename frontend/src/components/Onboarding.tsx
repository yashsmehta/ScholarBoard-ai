import { useState } from 'react'

interface OnboardingProps {
  onComplete: () => void
}

const steps = [
  {
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="1.5" />
        <circle cx="10" cy="13" r="2" fill="currentColor" opacity="0.5" />
        <circle cx="18" cy="11" r="2.5" fill="currentColor" opacity="0.7" />
        <circle cx="14" cy="19" r="2" fill="currentColor" opacity="0.5" />
        <circle cx="22" cy="17" r="1.5" fill="currentColor" opacity="0.4" />
        <circle cx="9" cy="20" r="1.5" fill="currentColor" opacity="0.4" />
      </svg>
    ),
    headline: 'Welcome to ScholarBoard.ai',
    description:
      'An interactive map of ~700 vision science researchers, arranged so that researchers working on similar topics appear near each other.',
  },
  {
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <rect x="3" y="3" width="26" height="26" rx="4" stroke="currentColor" strokeWidth="1.5" />
        <circle cx="11" cy="12" r="2" fill="currentColor" opacity="0.6" />
        <circle cx="20" cy="10" r="2.5" fill="currentColor" opacity="0.8" />
        <circle cx="15" cy="20" r="2" fill="currentColor" opacity="0.6" />
        <circle cx="23" cy="19" r="1.5" fill="currentColor" opacity="0.5" />
        <path d="M8 25l4-4m8 0l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
      </svg>
    ),
    headline: 'Explore the map',
    description:
      'Each dot is a researcher, colored by their primary research subfield. Scroll to zoom, drag to pan, hold Shift and drag to box-select.',
  },
  {
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <circle cx="14" cy="14" r="9" stroke="currentColor" strokeWidth="1.5" />
        <path d="M21 21l7 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M11 14h6M14 11v6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" opacity="0.5" />
      </svg>
    ),
    headline: 'Search & filter',
    description:
      'Find researchers by name with the search bar, or narrow the map by institution or subfield using filters.',
  },
  {
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <rect x="4" y="6" width="24" height="20" rx="3" stroke="currentColor" strokeWidth="1.5" />
        <circle cx="12" cy="14" r="3" stroke="currentColor" strokeWidth="1.3" />
        <path d="M18 12h6M18 16h4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" opacity="0.5" />
        <path d="M8 22h16" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" opacity="0.3" />
      </svg>
    ),
    headline: 'Dive deeper',
    description:
      "Click any dot to open a researcher's profile — their bio, recent papers, and an AI-generated research direction.",
  },
]

export function Onboarding({ onComplete }: OnboardingProps) {
  const [step, setStep] = useState(0)
  const isLast = step === steps.length - 1
  const current = steps[step]

  return (
    <div className="onboarding-overlay" onClick={onComplete} role="dialog" aria-modal="true" aria-label="Welcome tour">
      <div className="onboarding-panel" onClick={(e) => e.stopPropagation()}>
        <div className="onboarding-step">
          <div className="onboarding-step__icon">{current.icon}</div>
          <h2 className="onboarding-step__headline">{current.headline}</h2>
          <p className="onboarding-step__desc">{current.description}</p>
        </div>

        <div className="onboarding-dots" aria-hidden="true">
          {steps.map((_, i) => (
            <span key={i} className={`onboarding-dot${i === step ? ' is-active' : ''}`} />
          ))}
        </div>

        <div className="onboarding-nav">
          <button className="onboarding-skip" onClick={onComplete}>
            Skip
          </button>
          <button
            className="onboarding-next"
            onClick={() => (isLast ? onComplete() : setStep(step + 1))}
          >
            {isLast ? 'Start Exploring' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  )
}
