import { HeaderScene } from './HeaderScene'

interface HeaderProps {
  modeLabel?: string
  scholarCount?: number
}

export function Header({ modeLabel, scholarCount }: HeaderProps) {
  return (
    <header className="topbar">
      <HeaderScene />
      <div className="topbar__content">
        <h1 className="topbar__title">
          Scholar<span className="topbar__title-accent">Board</span>
          <span className="topbar__title-dot">.ai</span>
        </h1>
        <div className="topbar__right">
          {scholarCount != null && scholarCount > 0 && (
            <span className="topbar__stat">{scholarCount} scholars</span>
          )}
          {modeLabel && <span className="topbar__mode">{modeLabel}</span>}
        </div>
      </div>
    </header>
  )
}
