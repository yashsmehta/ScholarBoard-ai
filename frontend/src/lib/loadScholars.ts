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
