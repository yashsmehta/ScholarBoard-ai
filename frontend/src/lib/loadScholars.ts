import type { RawScholar, ResearchIdea, Scholar, ScholarLoadResult, SubfieldTag } from '../types/scholar'
import type { FrontendMode } from './appMode'
import { embeddedSampleSize } from './appMode'

type RawScholarMap = Record<string, RawScholar>

const DEFAULT_SOURCES = [
  import.meta.env.VITE_SCHOLARS_URL as string | undefined,
  '/api/scholars',
  `${import.meta.env.BASE_URL}data/build/scholars.json`,
].filter((value): value is string => Boolean(value))

const EMBEDDED_SOURCES = ['/embedded-scholars.json', ...DEFAULT_SOURCES]

interface LoadScholarsOptions {
  mode?: FrontendMode
}

export async function loadScholars(options: LoadScholarsOptions = {}): Promise<ScholarLoadResult> {
  const mode = options.mode ?? 'full'
  const failures: string[] = []
  const sources = mode === 'embedded' ? EMBEDDED_SOURCES : DEFAULT_SOURCES

  for (const source of sources) {
    try {
      const response = await fetch(source)
      if (!response.ok) {
        failures.push(`${source} (HTTP ${response.status})`)
        continue
      }

      const payload = (await response.json()) as unknown
      const normalized = normalizePayload(payload)
      const scholars =
        mode === 'embedded' && source !== '/embedded-scholars.json'
          ? normalized.slice(0, embeddedSampleSize())
          : normalized
      if (scholars.length === 0) {
        failures.push(`${source} (no valid scholars)`)
        continue
      }

      return {
        scholars,
        sourceLabel:
          mode === 'embedded'
            ? `Source: ${source}${source === '/embedded-scholars.json' ? '' : ` (embedded sample ${scholars.length})`}`
            : `Source: ${source}`,
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error'
      failures.push(`${source} (${message})`)
    }
  }

  throw new Error(`No scholar data source succeeded: ${failures.join('; ')}`)
}

function normalizePayload(payload: unknown): Scholar[] {
  let scholars: Scholar[]

  if (Array.isArray(payload)) {
    scholars = payload
      .map((value, index) => normalizeScholar(String(index), value as RawScholar))
      .filter((value): value is Scholar => value !== null)
  } else if (payload != null && typeof payload === 'object') {
    scholars = Object.entries(payload as RawScholarMap)
      .map(([id, value]) => normalizeScholar(id, value))
      .filter((value): value is Scholar => value !== null)
  } else {
    scholars = []
  }

  // Apply jitter to separate overlapping dots
  if (scholars.length > 0) {
    applyJitter(scholars)
  }

  return scholars
}

/**
 * Applies deterministic jitter to scholars whose (x, y) coordinates are
 * within a small threshold of each other, so overlapping dots become visible.
 * Non-overlapping scholars are not moved.
 */
function applyJitter(scholars: Scholar[]): void {
  if (scholars.length < 2) return

  // Compute bounding box diagonal
  let minX = Infinity,
    maxX = -Infinity,
    minY = Infinity,
    maxY = -Infinity
  for (const s of scholars) {
    if (s.x < minX) minX = s.x
    if (s.x > maxX) maxX = s.x
    if (s.y < minY) minY = s.y
    if (s.y > maxY) maxY = s.y
  }
  const diagonal = Math.sqrt((maxX - minX) ** 2 + (maxY - minY) ** 2)
  // EPS is 0.5% of diagonal — threshold for considering points "overlapping"
  const eps = diagonal * 0.005

  // Skip if data has no spread (degenerate case)
  if (diagonal === 0 || !Number.isFinite(eps)) return

  // Build spatial index: grid cells of size eps
  const cellSize = eps
  const grid = new Map<string, Scholar[]>()

  const cellKey = (x: number, y: number): string => {
    const cx = Math.floor(x / cellSize)
    const cy = Math.floor(y / cellSize)
    return `${cx},${cy}`
  }

  for (const s of scholars) {
    const key = cellKey(s.x, s.y)
    let cell = grid.get(key)
    if (!cell) {
      cell = []
      grid.set(key, cell)
    }
    cell.push(s)
  }

  // Track which scholars have been processed
  const processed = new Set<string>()

  // For each scholar, find nearby scholars and form clusters
  for (const s of scholars) {
    if (processed.has(s.id)) continue

    // Gather all scholars within eps distance (check own cell + neighbors)
    const cx = Math.floor(s.x / cellSize)
    const cy = Math.floor(s.y / cellSize)
    const cluster: Scholar[] = []

    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        const neighborKey = `${cx + dx},${cy + dy}`
        const neighborCell = grid.get(neighborKey)
        if (!neighborCell) continue
        for (const neighbor of neighborCell) {
          if (processed.has(neighbor.id)) continue
          const dist = Math.sqrt((s.x - neighbor.x) ** 2 + (s.y - neighbor.y) ** 2)
          if (dist < eps) {
            cluster.push(neighbor)
          }
        }
      }
    }

    // If cluster has only one member (no overlap), skip
    if (cluster.length <= 1) {
      processed.add(s.id)
      continue
    }

    // Mark all cluster members as processed
    for (const member of cluster) {
      processed.add(member.id)
    }

    // Compute centroid of original positions
    let centroidX = 0,
      centroidY = 0
    for (const member of cluster) {
      centroidX += member.x
      centroidY += member.y
    }
    centroidX /= cluster.length
    centroidY /= cluster.length

    // Sort cluster deterministically by id for stable layout
    cluster.sort((a, b) => a.id.localeCompare(b.id))

    // Distribute on a circle around centroid
    // Radius scales with sqrt(n) so larger clusters spread more
    const radius = eps * Math.sqrt(cluster.length) * 0.5
    const angleStep = (2 * Math.PI) / cluster.length

    for (let i = 0; i < cluster.length; i++) {
      const angle = i * angleStep
      cluster[i].x = centroidX + radius * Math.cos(angle)
      cluster[i].y = centroidY + radius * Math.sin(angle)
    }
  }
}

function normalizeScholar(fallbackId: string, raw: RawScholar): Scholar | null {
  const id = normalizeString(raw.id) ?? fallbackId
  const name = normalizeString(raw.name)
  const x = raw.umap_projection?.x
  const y = raw.umap_projection?.y

  if (!name || typeof x !== 'number' || typeof y !== 'number') return null

  return {
    id,
    name,
    institution: normalizeString(raw.institution),
    department: normalizeString(raw.department),
    labName: normalizeString(raw.lab_name),
    labUrl: normalizeString(raw.lab_url),
    mainResearchArea: normalizeString(raw.main_research_area),
    bio: normalizeString(raw.bio),
    researchDirection: normalizeString(raw.research_direction),
    totalCitations: typeof raw.total_citations === 'number' ? raw.total_citations : undefined,
    hIndex: typeof raw.h_index === 'number' ? raw.h_index : undefined,
    profilePic: normalizeString(raw.profile_pic),
    cluster: typeof raw.cluster === 'number' ? raw.cluster : -1,
    x,
    y,
    primarySubfield: normalizeString(raw.primary_subfield),
    subfields: Array.isArray(raw.subfields) ? raw.subfields.filter(isSubfieldLike) : [],
    papers: Array.isArray(raw.papers) ? raw.papers.filter(isPaperLike) : [],
    education: Array.isArray(raw.education) ? raw.education.filter(isObjectLike) : [],
    suggestedIdea: normalizeResearchIdea(raw.suggested_idea),
  }
}

function normalizeString(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined
  const trimmed = value.trim()
  if (!trimmed || /^(nan|null)$/i.test(trimmed)) return undefined
  return trimmed
}

function isObjectLike(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === 'object'
}

function isPaperLike(value: unknown): value is Scholar['papers'][number] {
  return isObjectLike(value) && typeof value.title === 'string' && (value.title as string).trim().length > 0
}

function isSubfieldLike(value: unknown): value is SubfieldTag {
  return isObjectLike(value) && typeof value.subfield === 'string' && typeof value.score === 'number'
}

function normalizeResearchIdea(raw: unknown): ResearchIdea | undefined {
  if (!isObjectLike(raw)) return undefined
  const r = raw as Record<string, unknown>
  const title = normalizeString(r.title)
  const hypothesis = normalizeString(r.hypothesis)
  if (!title || !hypothesis) return undefined
  return {
    researchThread: normalizeString(r.research_thread) ?? '',
    openQuestion: normalizeString(r.open_question) ?? '',
    title,
    hypothesis,
    approach: normalizeString(r.approach) ?? '',
    scientificImpact: normalizeString(r.scientific_impact) ?? '',
    whyNow: normalizeString(r.why_now) ?? '',
  }
}
