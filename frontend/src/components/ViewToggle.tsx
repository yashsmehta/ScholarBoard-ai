import type { ReactElement } from 'react'
import { cx } from '../lib/cx'
import type { ViewMode } from '../state/appReducer'

interface ViewToggleProps {
  viewMode: ViewMode
  onChange: (mode: ViewMode) => void
}

const OPTIONS: Array<{ mode: ViewMode; label: string; icon: ReactElement }> = [
  {
    mode: 'list',
    label: 'List',
    icon: (
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
        <line x1="5.5" y1="4" x2="14" y2="4" />
        <line x1="5.5" y1="8" x2="14" y2="8" />
        <line x1="5.5" y1="12" x2="14" y2="12" />
        <circle cx="2.4" cy="4" r="0.6" fill="currentColor" />
        <circle cx="2.4" cy="8" r="0.6" fill="currentColor" />
        <circle cx="2.4" cy="12" r="0.6" fill="currentColor" />
      </svg>
    ),
  },
  {
    mode: 'map',
    label: 'Map',
    icon: (
      <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <circle cx="4" cy="4" r="1.5" />
        <circle cx="10" cy="3" r="1.5" />
        <circle cx="7" cy="8" r="1.5" />
        <circle cx="12.5" cy="7.5" r="1.5" />
        <circle cx="3" cy="11.5" r="1.5" />
        <circle cx="9" cy="12.5" r="1.5" />
      </svg>
    ),
  },
]

/** Segmented List | Map switch that sits beside the search box. */
export function ViewToggle({ viewMode, onChange }: ViewToggleProps) {
  return (
    <div
      className={cx('view-toggle', viewMode === 'map' && 'view-toggle--map')}
      role="radiogroup"
      aria-label="View"
    >
      <span className="view-toggle__thumb" aria-hidden="true" />
      {OPTIONS.map(({ mode, label, icon }) => (
        <button
          key={mode}
          type="button"
          role="radio"
          aria-checked={viewMode === mode}
          className={cx('view-toggle__option', viewMode === mode && 'is-active')}
          onClick={() => viewMode !== mode && onChange(mode)}
          title={`${label} view`}
        >
          {icon}
          <span>{label}</span>
        </button>
      ))}
    </div>
  )
}
