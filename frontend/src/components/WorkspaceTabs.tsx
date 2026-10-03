import type { KeyboardEvent, ReactElement } from 'react'
import { cx } from '../lib/cx'

export type WorkspaceTab = 'directory' | 'ai'
export type AiSearchStatus = 'idle' | 'running' | 'done'

interface WorkspaceTabsProps {
  active: WorkspaceTab
  onChange: (tab: WorkspaceTab) => void
  aiStatus: AiSearchStatus
  aiCount: number
}

const TABS: Array<{ id: WorkspaceTab; label: string; icon: ReactElement }> = [
  {
    id: 'directory',
    label: 'Directory',
    icon: (
      <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <circle cx="4" cy="4.5" r="1.6" />
        <circle cx="10.5" cy="3.5" r="1.6" />
        <circle cx="7.5" cy="8.5" r="1.6" />
        <circle cx="12.5" cy="9.5" r="1.6" />
        <circle cx="3.5" cy="12" r="1.6" />
        <circle cx="9" cy="13.5" r="1.6" />
      </svg>
    ),
  },
  {
    id: 'ai',
    label: 'AI Search',
    icon: (
      <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <path d="M7 1.5c.35 2.9 1.6 4.15 4.5 4.5-2.9.35-4.15 1.6-4.5 4.5-.35-2.9-1.6-4.15-4.5-4.5 2.9-.35 4.15-1.6 4.5-4.5Z" />
        <path d="M12.25 9.5c.2 1.6.9 2.3 2.5 2.5-1.6.2-2.3.9-2.5 2.5-.2-1.6-.9-2.3-2.5-2.5 1.6-.2 2.3-.9 2.5-2.5Z" />
      </svg>
    ),
  },
]

export function WorkspaceTabs({ active, onChange, aiStatus, aiCount }: WorkspaceTabsProps) {
  // Arrow keys move between tabs (WAI-ARIA tabs pattern)
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    const next = TABS[(TABS.findIndex((t) => t.id === active) + 1) % TABS.length].id
    onChange(next)
    document.getElementById(`ws-tab-${next}`)?.focus()
  }

  return (
    <div className="ws-tabs" role="tablist" aria-label="Workspace" onKeyDown={onKeyDown}>
      {TABS.map((tab) => {
        const selected = tab.id === active
        return (
          <button
            key={tab.id}
            id={`ws-tab-${tab.id}`}
            type="button"
            role="tab"
            aria-selected={selected}
            aria-controls={`ws-panel-${tab.id}`}
            tabIndex={selected ? 0 : -1}
            className={cx('ws-tab', `ws-tab--${tab.id}`, selected && 'is-active')}
            onClick={() => onChange(tab.id)}
          >
            <span className="ws-tab__icon">{tab.icon}</span>
            <span className="ws-tab__label">{tab.label}</span>
            {tab.id === 'ai' && aiStatus === 'running' && (
              <span className="ws-tab__spinner" aria-label="AI search running" />
            )}
            {tab.id === 'ai' && aiStatus === 'done' && aiCount > 0 && (
              <span className="ws-tab__count" aria-label={`${aiCount} results`}>{aiCount}</span>
            )}
          </button>
        )
      })}
    </div>
  )
}
