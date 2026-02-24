import * as d3 from 'd3'
import type { Scholar } from '../types/scholar'
import { clusterColor } from './colorScale'

const DOT_RADIUS = 4.2
const DOT_RADIUS_HOVER = 6.2
const DOT_RADIUS_SELECTED = 8.4
const BASE_STROKE = 'rgba(255,255,255,0.84)'
const SELECTED_STROKE = '#112136'
const MAP_PADDING = 72

export interface MapInteractionState {
  hoveredScholarId: string | null
  selectedScholarId: string | null
  activeInstitutions: Set<string>
}

export interface D3MapCallbacks {
  onHoverScholarId: (scholarId: string | null) => void
  onSelectScholarId: (scholarId: string | null) => void
}

export interface D3MapController {
  setData: (scholars: Scholar[]) => void
  setInteractionState: (state: MapInteractionState) => void
  resize: () => void
  resetView: () => void
  panToScholar: (scholarId: string, scale?: number) => void
  destroy: () => void
}

export function createD3MapController(
  container: HTMLElement,
  callbacks: D3MapCallbacks,
): D3MapController {
  const svg = d3.select(container).append('svg').attr('class', 'scholar-map__svg')
  const root = svg.append('g').attr('class', 'scholar-map__zoom-root')
  const ringLayer = root.append('g').attr('class', 'scholar-map__ring-layer')
  const dotLayer = root.append('g').attr('class', 'scholar-map__dot-layer')
  const brushLayer = svg.append('g').attr('class', 'scholar-map__brush-layer')
  const selectionRing = ringLayer
    .append('circle')
    .attr('class', 'scholar-map__selection-ring')
    .style('display', 'none')
  const tooltipEl = document.createElement('div')
  tooltipEl.className = 'scholar-map__tooltip'
  tooltipEl.innerHTML =
    '<div class="scholar-map__tooltip-name"></div><div class="scholar-map__tooltip-institution"></div>'
  container.appendChild(tooltipEl)

  let dots = dotLayer.selectAll<SVGCircleElement, Scholar>('circle.scholar-map__dot')
  let scholars: Scholar[] = []
  let xScale = d3.scaleLinear()
  let yScale = d3.scaleLinear()
  let currentTransform = d3.zoomIdentity
  let boxZoomModifierActive = false
  let pointerDownSnapshot: {
    x: number
    y: number
    targetWasDot: boolean
    targetScholarId: string | null
    transformX: number
    transformY: number
    transformK: number
  } | null = null
  let interactionState: MapInteractionState = {
    hoveredScholarId: null,
    selectedScholarId: null,
    activeInstitutions: new Set<string>(),
  }

  const zoom = d3
    .zoom<SVGSVGElement, unknown>()
    .filter((event) => {
      if (event.type === 'wheel') return true
      if (event.type === 'mousedown' || event.type === 'pointerdown') {
        return (event.button ?? 0) === 0 && !boxZoomModifierActive
      }
      return !boxZoomModifierActive
    })
    .clickDistance(6)
    .tapDistance(12)
    .scaleExtent([0.3, 20])
    .on('zoom', (event) => {
      currentTransform = event.transform
      root.attr('transform', event.transform.toString())
      hideTooltip()
    })

  svg.call(zoom)
  svg.on('dblclick.zoom', null)
  svg.on('pointerdown.selection', (event) => {
    if ((event.button ?? 0) !== 0) return
    const [x, y] = d3.pointer(event, svg.node())
    const target = event.target as Element | null
    const targetDot = target?.closest?.('.scholar-map__dot') as (SVGCircleElement & {
      __data__?: Scholar
    }) | null
    pointerDownSnapshot = {
      x,
      y,
      targetWasDot: Boolean(targetDot),
      targetScholarId: targetDot?.__data__?.id ?? null,
      transformX: currentTransform.x,
      transformY: currentTransform.y,
      transformK: currentTransform.k,
    }
  })
  svg.on('pointerup.selection', (event) => {
    if (!pointerDownSnapshot) return
    const snapshot = pointerDownSnapshot
    pointerDownSnapshot = null
    if ((event.button ?? 0) !== 0 || boxZoomModifierActive) return

    const [x, y] = d3.pointer(event, svg.node())
    const pointerMove = Math.hypot(x - snapshot.x, y - snapshot.y)
    const transformMove =
      Math.abs(currentTransform.x - snapshot.transformX) +
      Math.abs(currentTransform.y - snapshot.transformY) +
      Math.abs(currentTransform.k - snapshot.transformK)

    // Ignore actual pans/zooms, but allow small click jitter on trackpads.
    if (pointerMove > 14 || transformMove > 0.0001) return

    if (snapshot.targetScholarId) {
      callbacks.onSelectScholarId(snapshot.targetScholarId)
      callbacks.onHoverScholarId(snapshot.targetScholarId)
      return
    }

    // If native dot click fires, this is harmless duplication; selection is idempotent.
    const candidate = findNearestVisibleScholarAtViewportPoint(x, y, 16)
    if (!candidate) return
    callbacks.onSelectScholarId(candidate.id)
    callbacks.onHoverScholarId(candidate.id)
  })
  svg.on('dblclick', (event) => {
    const [px, py] = d3.pointer(event, svg.node())
    const factor = event.shiftKey ? 1 / 1.8 : 1.8
    zoomAtPoint(px, py, factor)
  })

  const brush = d3
    .brush()
    .keyModifiers(false)
    .filter((event) => {
      return (
        (event.type === 'mousedown' || event.type === 'pointerdown') &&
        (event.button ?? 0) === 0 &&
        boxZoomModifierActive
      )
    })
    .on('start', () => {
      hideTooltip()
    })
    .on('end', onBrushEnd)

  brushLayer.call(brush)
  updateBrushLayerInteractivity()

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key !== 'Shift') return
    setBoxZoomModifier(true)
  }

  const onKeyUp = (event: KeyboardEvent) => {
    if (event.key !== 'Shift') return
    setBoxZoomModifier(false)
  }

  const onWindowBlur = () => {
    setBoxZoomModifier(false)
  }

  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  window.addEventListener('blur', onWindowBlur)
  updateBoxZoomModifierUI()
  container.classList.add('scholar-map--interactive')

  function setData(nextScholars: Scholar[]) {
    scholars = nextScholars
    resize()
    renderDots()
    refreshDotStyles()
    updateSelectionRing()
  }

  function setInteractionState(nextState: MapInteractionState) {
    interactionState = nextState
    refreshDotStyles()
    updateSelectionRing()
  }

  function renderDots() {
    dots = dotLayer
      .selectAll<SVGCircleElement, Scholar>('circle.scholar-map__dot')
      .data(scholars, (datum) => datum.id)
      .join(
        (enter) =>
          enter
            .append('circle')
            .attr('class', 'scholar-map__dot')
            .attr('r', DOT_RADIUS)
            .attr('fill-opacity', (d) => (d.cluster < 0 ? 0.64 : 0.96))
            .attr('stroke', BASE_STROKE)
            .attr('stroke-width', 1)
            .on('pointerdown', (event, d) => {
              recordPointerDownSnapshot(event, d)
              try {
                ;(event.currentTarget as SVGCircleElement).setPointerCapture?.(event.pointerId)
              } catch {
                // Pointer capture can fail on some browsers/input types; selection still falls back.
              }
              // Prevent zoom from stealing click selection on dot presses.
              event.stopPropagation()
            })
            .on('mousedown', (event) => {
              event.stopPropagation()
            })
            .on('mouseenter', function (_event, d) {
              callbacks.onHoverScholarId(d.id)
              raiseDot(this as SVGCircleElement)
            })
            .on('mousemove', (event, d) => showTooltip(event, d))
            .on('mouseleave', () => {
              callbacks.onHoverScholarId(null)
              hideTooltip()
            })
            .on('pointerup', (event, d) => {
              if ((event.button ?? 0) !== 0) return
              event.stopPropagation()
              raiseDot(event.currentTarget as SVGCircleElement)
              callbacks.onSelectScholarId(d.id)
            }),
        (update) => update,
        (exit) => exit.remove(),
      )
      .attr('cx', (d) => xScale(d.x))
      .attr('cy', (d) => yScale(d.y))
      .attr('fill', (d) => clusterColor(d.cluster))

    svg.on('click', () => {
      callbacks.onHoverScholarId(null)
      hideTooltip()
    })
  }

  function refreshDotStyles() {
    dots.each(function applyStyle(datum) {
      const isSelected = interactionState.selectedScholarId === datum.id
      const isHovered = interactionState.hoveredScholarId === datum.id && !isSelected
      const institution = datum.institution ?? 'Unknown'
      const filterActive = interactionState.activeInstitutions.size > 0
      const isVisible = !filterActive || interactionState.activeInstitutions.has(institution)

      d3.select(this)
        .attr('r', isSelected ? DOT_RADIUS_SELECTED : isHovered ? DOT_RADIUS_HOVER : DOT_RADIUS)
        .attr('stroke', isSelected ? SELECTED_STROKE : BASE_STROKE)
        .attr('stroke-width', isSelected ? 3 : isHovered ? 1.9 : 0.95)
        .attr('opacity', isVisible ? 1 : 0.08)
        .style('pointer-events', isVisible ? 'auto' : 'none')
    })
  }

  function updateSelectionRing() {
    const selectedScholar = interactionState.selectedScholarId
      ? scholars.find((scholar) => scholar.id === interactionState.selectedScholarId)
      : undefined

    if (!selectedScholar) {
      selectionRing.style('display', 'none')
      return
    }

    selectionRing
      .style('display', null)
      .attr('cx', xScale(selectedScholar.x))
      .attr('cy', yScale(selectedScholar.y))
      .attr('r', DOT_RADIUS_SELECTED + 6.8)
  }

  function resize() {
    const width = container.clientWidth || 640
    const height = container.clientHeight || 480
    const pad = Math.max(42, Math.min(MAP_PADDING, Math.min(width, height) * 0.12))

    svg.attr('width', width).attr('height', height)
    brush.extent([
      [0, 0],
      [width, height],
    ])
    brushLayer.call(brush)
    updateBrushLayerInteractivity()

    if (scholars.length > 0) {
      const xExtent = d3.extent(scholars, (d) => d.x) as [number, number]
      const yExtent = d3.extent(scholars, (d) => d.y) as [number, number]
      xScale = d3.scaleLinear().domain(paddedExtent(xExtent)).range([pad, width - pad])
      yScale = d3.scaleLinear().domain(paddedExtent(yExtent)).range([pad, height - pad])
    } else {
      xScale = d3.scaleLinear().domain([0, 1]).range([pad, width - pad])
      yScale = d3.scaleLinear().domain([0, 1]).range([pad, height - pad])
    }

    dots.attr('cx', (d) => xScale(d.x)).attr('cy', (d) => yScale(d.y))
    updateSelectionRing()
  }

  function resetView() {
    hideTooltip()
    clearBrushSelection()
    svg.transition().duration(220).call(zoom.transform, d3.zoomIdentity)
  }

  function panToScholar(scholarId: string, scale = 3) {
    const scholar = scholars.find((item) => item.id === scholarId)
    if (!scholar) return
    const width = container.clientWidth || 640
    const height = container.clientHeight || 480
    const sx = xScale(scholar.x)
    const sy = yScale(scholar.y)
    hideTooltip()
    clearBrushSelection()
    svg
      .transition()
      .duration(260)
      .call(
        zoom.transform,
        d3.zoomIdentity.translate(width / 2, height / 2).scale(scale).translate(-sx, -sy),
      )
  }

  function zoomAtPoint(px: number, py: number, factor: number) {
    const targetK = Math.max(0.3, Math.min(20, currentTransform.k * factor))
    const localX = currentTransform.invertX(px)
    const localY = currentTransform.invertY(py)
    const nextTransform = d3.zoomIdentity
      .translate(px, py)
      .scale(targetK)
      .translate(-localX, -localY)
    svg.transition().duration(180).call(zoom.transform, nextTransform)
  }

  function destroy() {
    svg.interrupt()
    window.removeEventListener('keydown', onKeyDown)
    window.removeEventListener('keyup', onKeyUp)
    window.removeEventListener('blur', onWindowBlur)
    tooltipEl.remove()
    svg.remove()
  }

  return { setData, setInteractionState, resize, resetView, panToScholar, destroy }

  function updateBoxZoomModifierUI() {
    container.classList.toggle('is-box-zoom-mode', boxZoomModifierActive)
  }

  function updateBrushLayerInteractivity() {
    if (boxZoomModifierActive) {
      brushLayer.style('display', null)
      brushLayer.style('pointer-events', 'all')
      brushLayer.selectAll('*').style('pointer-events', null)
    } else {
      brushLayer.style('display', 'none')
      brushLayer.style('pointer-events', 'none')
      brushLayer.selectAll('*').style('pointer-events', 'none')
    }
    brushLayer.classed('is-active', boxZoomModifierActive)
  }

  function clearBrushSelection() {
    brushLayer.call(brush.move, null)
  }

  function setBoxZoomModifier(active: boolean) {
    if (boxZoomModifierActive === active) return
    boxZoomModifierActive = active
    if (!active) clearBrushSelection()
    updateBoxZoomModifierUI()
    updateBrushLayerInteractivity()
  }

  function onBrushEnd(event: d3.D3BrushEvent<unknown>) {
    if (!event.selection) return

    const [[x0, y0], [x1, y1]] = event.selection as [[number, number], [number, number]]
    const width = Math.abs(x1 - x0)
    const height = Math.abs(y1 - y0)
    clearBrushSelection()

    if (width < 12 || height < 12) return

    const minX = Math.min(x0, x1)
    const maxX = Math.max(x0, x1)
    const minY = Math.min(y0, y1)
    const maxY = Math.max(y0, y1)

    const lx0 = currentTransform.invertX(minX)
    const lx1 = currentTransform.invertX(maxX)
    const ly0 = currentTransform.invertY(minY)
    const ly1 = currentTransform.invertY(maxY)

    const localWidth = Math.max(1, Math.abs(lx1 - lx0))
    const localHeight = Math.max(1, Math.abs(ly1 - ly0))
    const cx = (lx0 + lx1) / 2
    const cy = (ly0 + ly1) / 2

    const viewW = container.clientWidth || 640
    const viewH = container.clientHeight || 480
    const targetScale = Math.max(0.3, Math.min(20, Math.min(viewW / localWidth, viewH / localHeight) * 0.94))
    const target = d3.zoomIdentity
      .translate(viewW / 2, viewH / 2)
      .scale(targetScale)
      .translate(-cx, -cy)

    svg.transition().duration(220).call(zoom.transform, target)
  }

  function showTooltip(event: MouseEvent, scholar: Scholar) {
    const nameEl = tooltipEl.querySelector('.scholar-map__tooltip-name')
    const institutionEl = tooltipEl.querySelector('.scholar-map__tooltip-institution')
    if (nameEl) nameEl.textContent = scholar.name
    if (institutionEl) institutionEl.textContent = scholar.institution ?? 'Unknown institution'

    tooltipEl.classList.add('is-visible')
    positionTooltip(event)
  }

  function hideTooltip() {
    tooltipEl.classList.remove('is-visible')
  }

  function positionTooltip(event: MouseEvent) {
    if (!tooltipEl.classList.contains('is-visible')) return
    const containerRect = container.getBoundingClientRect()
    const tooltipRect = tooltipEl.getBoundingClientRect()
    let x = event.clientX - containerRect.left + 14
    let y = event.clientY - containerRect.top - tooltipRect.height - 10

    if (x + tooltipRect.width > containerRect.width - 8) {
      x = containerRect.width - tooltipRect.width - 8
    }
    if (x < 8) x = 8
    if (y < 8) y = event.clientY - containerRect.top + 14

    tooltipEl.style.left = `${x}px`
    tooltipEl.style.top = `${y}px`
  }

  function raiseDot(node: SVGCircleElement) {
    node.parentNode?.appendChild(node)
  }

  function recordPointerDownSnapshot(event: PointerEvent, scholar: Scholar) {
    const [x, y] = d3.pointer(event, svg.node())
    pointerDownSnapshot = {
      x,
      y,
      targetWasDot: true,
      targetScholarId: scholar.id,
      transformX: currentTransform.x,
      transformY: currentTransform.y,
      transformK: currentTransform.k,
    }
  }

  function findNearestVisibleScholarAtViewportPoint(
    viewportX: number,
    viewportY: number,
    maxDistancePx: number,
  ): Scholar | null {
    let best: { scholar: Scholar; dist: number } | null = null

    for (const scholar of scholars) {
      const institution = scholar.institution ?? 'Unknown'
      if (
        interactionState.activeInstitutions.size > 0 &&
        !interactionState.activeInstitutions.has(institution)
      ) {
        continue
      }

      const localX = xScale(scholar.x)
      const localY = yScale(scholar.y)
      const screenX = currentTransform.applyX(localX)
      const screenY = currentTransform.applyY(localY)
      const dist = Math.hypot(screenX - viewportX, screenY - viewportY)

      if (dist > maxDistancePx) continue
      if (!best || dist < best.dist) {
        best = { scholar, dist }
      }
    }

    return best?.scholar ?? null
  }
}

function paddedExtent(extent: [number, number]): [number, number] {
  const [min, max] = extent
  if (Number.isNaN(min) || Number.isNaN(max)) return [0, 1]
  if (min === max) return [min - 1, max + 1]
  return [min, max]
}
