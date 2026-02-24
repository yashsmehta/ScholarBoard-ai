import type { RawScholar, Scholar, ScholarLoadResult } from '../types/scholar'
import type { FrontendMode } from './appMode'
import { embeddedSampleSize } from './appMode'

type RawScholarMap = Record<string, RawScholar>

const DEFAULT_SOURCES = [
  import.meta.env.VITE_SCHOLARS_URL as string | undefined,
  '/api/scholars',
  '/data/scholars.json',
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
  if (Array.isArray(payload)) {
    return payload
      .map((value, index) => normalizeScholar(String(index), value as RawScholar))
      .filter((value): value is Scholar => value !== null)
  }

  if (payload != null && typeof payload === 'object') {
    return Object.entries(payload as RawScholarMap)
      .map(([id, value]) => normalizeScholar(id, value))
      .filter((value): value is Scholar => value !== null)
  }

  return []
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
    bio: normalizeString(raw.bio),
    profilePic: normalizeString(raw.profile_pic),
    cluster: typeof raw.cluster === 'number' ? raw.cluster : -1,
    x,
    y,
    researchAreas: Array.isArray(raw.research_areas)
      ? raw.research_areas.filter(isNonEmptyString)
      : [],
    papers: Array.isArray(raw.papers) ? raw.papers.filter(isPaperLike) : [],
    education: Array.isArray(raw.education) ? raw.education.filter(isEducationLike) : [],
  }
}

function normalizeString(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined
  const trimmed = value.trim()
  if (!trimmed) return undefined
  if (trimmed.toLowerCase() === 'nan') return undefined
  if (trimmed.toLowerCase() === 'null') return undefined
  return trimmed
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0
}

function isPaperLike(value: unknown): value is Scholar['papers'][number] {
  if (value == null || typeof value !== 'object') return false
  const candidate = value as { title?: unknown }
  return typeof candidate.title === 'string' && candidate.title.trim().length > 0
}

function isEducationLike(value: unknown): value is Scholar['education'][number] {
  return value != null && typeof value === 'object'
}
