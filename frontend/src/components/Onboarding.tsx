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
        <circle cx="18" cy="11" r="2.5" fill="currentColor" opacity="0.8" />
        <circle cx="14" cy="19" r="2" fill="currentColor" opacity="0.5" />
        <circle cx="22" cy="17" r="1.5" fill="currentColor" opacity="0.4" />
        <circle cx="9" cy="20" r="1.5" fill="currentColor" opacity="0.4" />
      </svg>
    ),
    headline: '~800 vision scientists, arranged by similarity',
    description: 'Each dot is a researcher. The closer two dots, the more their work overlaps. Colors reflect each researcher\'s primary subfield.',
  },
  {
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <circle cx="16" cy="15" r="7" stroke="currentColor" strokeWidth="1.5" />
        <path d="M12 15h8M16 11v8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" opacity="0.5" />
        <path d="M4 15h5M23 15h5M16 4v5M16 23v5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" opacity="0.25" />
      </svg>
    ),
    headline: 'Navigate with scroll, drag, and click',
    description: 'Scroll to zoom in on a cluster. Drag to pan. Click any dot to open that researcher\'s profile.',
  },
  {
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <rect x="4" y="6" width="24" height="20" rx="3" stroke="currentColor" strokeWidth="1.5" />
        <circle cx="12" cy="14" r="3" stroke="currentColor" strokeWidth="1.3" />
        <path d="M18 12h8M18 16h5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" opacity="0.5" />
        <path d="M8 22h16" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" opacity="0.25" />
      </svg>
    ),
    headline: 'Each profile has papers, bio, and an AI research idea',
    description: 'Click a dot to see their recent publications and an AI-generated suggestion for where their work could go next.',
  },
  {
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <circle cx="13" cy="13" r="8" stroke="currentColor" strokeWidth="1.5" />
        <path d="M19 19l8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M4 26h10M4 22h7" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" opacity="0.35" />
      </svg>
    ),
    headline: 'Search, filter, and explore field directions',
    description: 'Find anyone by name top-left. Filter by institution or subfield top-right. Hit "Field Directions" in the header to see what each research community is collectively working on.',
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
            {isLast ? 'Start Exploring' : 'Next →'}
          </button>
        </div>
      </div>
    </div>
  )
}
