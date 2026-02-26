import { useEffect, useMemo, useRef } from 'react'
import type { Scholar } from '../types/scholar'
import {
  createD3MapController,
  type D3MapController,
  type MapInteractionState,
} from '../map/d3MapController'

interface ScholarMapProps {
  scholars: Scholar[]
  activeInstitutions: string[]
  activeSubfields: string[]
  hoveredScholarId: string | null
  selectedScholarId: string | null
  resetNonce: number
  panRequest: { scholarId: string; nonce: number } | null
  onHoverScholarId: (scholarId: string | null) => void
  onSelectScholarId: (scholarId: string | null) => void
}

export function ScholarMap({
  scholars,
  activeInstitutions,
  activeSubfields,
  hoveredScholarId,
  selectedScholarId,
  resetNonce,
  panRequest,
  onHoverScholarId,
  onSelectScholarId,
}: ScholarMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const controllerRef = useRef<D3MapController | null>(null)
  const hoverHandlerRef = useRef(onHoverScholarId)
  const selectHandlerRef = useRef(onSelectScholarId)

  const interactionState: MapInteractionState = useMemo(
    () => ({
      hoveredScholarId,
      selectedScholarId,
      activeInstitutions: new Set(activeInstitutions),
      activeSubfields: new Set(activeSubfields),
    }),
    [hoveredScholarId, selectedScholarId, activeInstitutions, activeSubfields],
  )

  useEffect(() => {
    hoverHandlerRef.current = onHoverScholarId
  }, [onHoverScholarId])

  useEffect(() => {
    selectHandlerRef.current = onSelectScholarId
  }, [onSelectScholarId])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const controller = createD3MapController(container, {
      onHoverScholarId: (scholarId) => hoverHandlerRef.current(scholarId),
      onSelectScholarId: (scholarId) => selectHandlerRef.current(scholarId),
    })
    controllerRef.current = controller
    controller.setData(scholars)
    controller.setInteractionState(interactionState)

    const resizeObserver = new ResizeObserver(() => {
      controller.resize()
    })
    resizeObserver.observe(container)

    return () => {
      resizeObserver.disconnect()
      controller.destroy()
      controllerRef.current = null
    }
  }, [])

  useEffect(() => {
    controllerRef.current?.setData(scholars)
  }, [scholars])

  useEffect(() => {
    controllerRef.current?.setInteractionState(interactionState)
  }, [interactionState])

  useEffect(() => {
    controllerRef.current?.resetView()
  }, [resetNonce])

  useEffect(() => {
    if (!panRequest) return
    controllerRef.current?.panToScholar(panRequest.scholarId)
  }, [panRequest?.nonce])

  return (
    <div className="scholar-map-shell">
      <div ref={containerRef} className="scholar-map" />
    </div>
  )
}
