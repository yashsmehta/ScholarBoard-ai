interface MapControlsProps {
  onReset: () => void
  hint: string
}

export function MapControls({ onReset, hint }: MapControlsProps) {
  return (
      <>
      <div className="map-overlay map-overlay-bottom-left">
        <p className="map-hint">{hint}</p>
      </div>
      <div className="map-overlay map-overlay-bottom-right">
        <div className="map-controls">
          <button type="button" className="icon-button" onClick={onReset}>
            Reset View
          </button>
        </div>
      </div>
    </>
  )
}
