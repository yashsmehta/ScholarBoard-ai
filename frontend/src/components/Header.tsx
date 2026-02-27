interface HeaderProps {
  modeLabel?: string
  onFieldDirectionsClick?: () => void
  onMethodologyClick?: () => void
  onTourClick?: () => void
}

export function Header({ modeLabel, onFieldDirectionsClick, onMethodologyClick, onTourClick }: HeaderProps) {
  return (
    <header className="topbar">
      <div className="topbar__content">
        <div className="topbar__left">
          <h1 className="topbar__title">
            Scholar<span className="topbar__title-accent">Board</span>
            <span className="topbar__title-dot">.ai</span>
          </h1>
        </div>
        <div className="topbar__right">
          <button className="topbar__method-btn" onClick={onFieldDirectionsClick}>
            Field Directions
          </button>
          <button className="topbar__method-btn" onClick={onMethodologyClick}>
            Methodology
          </button>
          <button className="topbar__tour-btn" onClick={onTourClick} aria-label="Take a tour" title="Take a tour">
            ?
          </button>
          {modeLabel && <span className="topbar__mode">{modeLabel}</span>}
        </div>
      </div>
    </header>
  )
}
