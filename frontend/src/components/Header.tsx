import type { ViewMode } from '../state/appReducer'

interface HeaderProps {
  modeLabel?: string
  scholarCount?: number
  viewMode: ViewMode
  onToggleView: () => void
  onMethodologyClick?: () => void
}

export function Header({ modeLabel, scholarCount, viewMode, onToggleView, onMethodologyClick }: HeaderProps) {
  return (
    <header className="topbar">
      <div className="topbar__content">
        <h1 className="topbar__title">
          Scholar<span className="topbar__title-accent">Board</span>
          <span className="topbar__title-dot">.ai</span>
        </h1>
        <div className="topbar__right">
          <button
            className="view-toggle"
            onClick={onToggleView}
            aria-label={viewMode === 'map' ? 'Switch to list view' : 'Switch to map view'}
            title={viewMode === 'map' ? 'List view' : 'Map view'}
          >
            {viewMode === 'map' ? (
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                <rect x="1" y="1" width="6" height="6" rx="1" />
                <rect x="9" y="1" width="6" height="6" rx="1" />
                <rect x="1" y="9" width="6" height="6" rx="1" />
                <rect x="9" y="9" width="6" height="6" rx="1" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <circle cx="4" cy="4" r="1.5" />
                <circle cx="10" cy="3" r="1.5" />
                <circle cx="7" cy="8" r="1.5" />
                <circle cx="12" cy="7" r="1.5" />
                <circle cx="3" cy="11" r="1.5" />
                <circle cx="9" cy="12" r="1.5" />
                <circle cx="14" cy="11" r="1.5" />
              </svg>
            )}
            <span>{viewMode === 'map' ? 'List' : 'Map'}</span>
          </button>
          {scholarCount != null && scholarCount > 0 && (
            <span className="topbar__stat">{scholarCount} scholars</span>
          )}
          <button className="topbar__method-btn" onClick={onMethodologyClick}>
            Methodology
          </button>
          {modeLabel && <span className="topbar__mode">{modeLabel}</span>}
        </div>
      </div>
    </header>
  )
}
