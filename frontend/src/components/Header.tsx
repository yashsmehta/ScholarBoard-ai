interface HeaderProps {
  modeLabel?: string
}

export function Header({ modeLabel }: HeaderProps) {
  return (
    <header className="topbar">
      <div className="topbar__content">
        <div className="topbar__badge">
          React + D3 Migration
          {modeLabel ? ` · ${modeLabel}` : ''}
        </div>
        <h1 className="topbar__title">ScholarBoard.ai</h1>
        <p className="topbar__subtitle">Explore scholars visually with a typed, modular frontend shell.</p>
      </div>
    </header>
  )
}
