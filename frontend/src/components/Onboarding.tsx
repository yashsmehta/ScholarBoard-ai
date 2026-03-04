import { useState, useEffect, useRef } from 'react'
import { cx } from '../lib/cx'

interface OnboardingProps {
  onComplete: () => void
}

type Phase = 'idle' | 'stepping' | 'dismissing'

const steps = [
  {
    image: `${import.meta.env.BASE_URL}onboarding/step1_map.jpg`,
    headline: '~800 vision scientists, one living map',
    description:
      "Each dot is a researcher. The closer two dots are, the more their work overlaps. Colors reflect each researcher's primary subfield.",
  },
  {
    image: `${import.meta.env.BASE_URL}onboarding/step2_navigate.jpg`,
    headline: 'Zoom, drag, and discover',
    description:
      "Scroll to zoom into a cluster. Drag to pan across the landscape. Click any dot to open that researcher's profile.",
  },
  {
    image: `${import.meta.env.BASE_URL}onboarding/step3_profile.jpg`,
    headline: 'Papers, bio, and an AI research idea',
    description:
      'Each profile shows recent publications and an AI-generated suggestion for where their work could go next.',
  },
  {
    image: `${import.meta.env.BASE_URL}onboarding/step4_search.jpg`,
    headline: 'Search, filter, explore field directions',
    description:
      'Find anyone by name. Filter by institution or subfield. Open "Field Directions" to see what each community is collectively working on.',
  },
]

export function Onboarding({ onComplete }: OnboardingProps) {
  const [step, setStep] = useState(0)
  const [phase, setPhase] = useState<Phase>('idle')
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const isLast = step === steps.length - 1
  const current = steps[step]

  // Preload all step images on mount
  useEffect(() => {
    steps.forEach((s) => {
      const img = new Image()
      img.src = s.image
    })
  }, [])

  // Cleanup pending timers on unmount
  useEffect(() => () => clearTimeout(timerRef.current), [])

  const goToStep = (next: number) => {
    if (phase !== 'idle') return
    setPhase('stepping')
    timerRef.current = setTimeout(() => {
      setStep(next)
      setPhase('idle')
    }, 280)
  }

  const handleClose = () => {
    if (phase !== 'idle') return
    setPhase('dismissing')
    timerRef.current = setTimeout(onComplete, 350)
  }

  const stepping = phase === 'stepping'

  return (
    <div
      className={cx('onboarding-overlay', phase === 'dismissing' && 'is-dismissing')}
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-label="Welcome tour"
    >
      <div className="onboarding-panel" onClick={(e) => e.stopPropagation()}>
        <button className="onboarding-close" onClick={handleClose} aria-label="Close tour">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>

        <div className="onboarding-illustration">
          <img
            key={step}
            src={current.image}
            alt=""
            className={cx('onboarding-illustration__img', stepping && 'is-exiting')}
          />
          <div className="onboarding-illustration__vignette" />
        </div>

        <div className={cx('onboarding-content', stepping && 'is-exiting')} key={`content-${step}`}>
          <div className="onboarding-step-badge">
            {step + 1} / {steps.length}
          </div>
          <h2 className="onboarding-headline">{current.headline}</h2>
          <p className="onboarding-desc">{current.description}</p>
        </div>

        <div className="onboarding-footer">
          <div className="onboarding-dots">
            {steps.map((_, i) => (
              <button
                key={i}
                className={cx('onboarding-dot', i === step && 'is-active', i < step && 'is-done')}
                onClick={() => goToStep(i)}
                aria-label={`Step ${i + 1}`}
              />
            ))}
          </div>
          <div className="onboarding-nav">
            <button className="onboarding-skip" onClick={handleClose}>
              Skip
            </button>
            <button
              className="onboarding-next"
              onClick={() => (isLast ? handleClose() : goToStep(step + 1))}
            >
              {isLast ? 'Start Exploring' : 'Next'}
              {!isLast && (
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M5 3l4 4-4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
