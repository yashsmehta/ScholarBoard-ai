export type FrontendMode = 'full' | 'embedded'

const EMBEDDED_MODE_PARAM = 'embedded'

export function detectFrontendMode(): FrontendMode {
  const queryMode = readQueryMode()
  if (queryMode) return queryMode

  const envMode = normalizeMode(import.meta.env.VITE_FRONTEND_MODE as string | undefined)
  return envMode ?? 'full'
}

function readQueryMode(): FrontendMode | null {
  if (typeof window === 'undefined') return null
  const params = new URLSearchParams(window.location.search)
  const mode = normalizeMode(params.get('mode') ?? undefined)
  return mode
}

function normalizeMode(value: string | undefined): FrontendMode | null {
  if (!value) return null
  const normalized = value.trim().toLowerCase()
  if (normalized === EMBEDDED_MODE_PARAM) return 'embedded'
  if (normalized === 'full') return 'full'
  return null
}

export function embeddedSampleSize(): number {
  const raw = import.meta.env.VITE_EMBEDDED_SAMPLE_SIZE as string | undefined
  const parsed = Number.parseInt(raw ?? '', 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 100
}
