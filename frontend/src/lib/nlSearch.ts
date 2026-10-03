/** Client for the natural-language PI search API (server/app.py). */

export interface AskResult {
  id: string
  score: number
  reason: string
}

interface JobResponse {
  job_id: string
  status: 'queued' | 'running' | 'done' | 'error'
  results?: AskResult[]
  error?: string
  queue_position?: number
}

export type AskEngine = 'agy' | 'claude'

export const ENGINE_LABELS: Record<AskEngine, string> = { agy: 'Antigravity', claude: 'Claude Code' }

export interface AskProgress {
  status: 'queued' | 'running'
  queuePosition: number
}

/** API origin; empty string disables the Ask feature. */
export const NL_SEARCH_API: string =
  (import.meta.env.VITE_NL_SEARCH_API as string | undefined) ?? (import.meta.env.DEV ? 'http://localhost:8001' : '')

const POLL_MS = 2000

async function readJob(response: Response): Promise<JobResponse> {
  if (!response.ok) {
    let detail = `Search failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      /* keep the generic message */
    }
    throw new Error(detail)
  }
  return response.json()
}

function wait(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms)
    signal.addEventListener('abort', () => {
      clearTimeout(timer)
      reject(new DOMException('Aborted', 'AbortError'))
    }, { once: true })
  })
}

/** Engines the server offers (first is its default); [] if the API is unreachable. */
export async function fetchEngines(): Promise<AskEngine[]> {
  try {
    const health = await (await fetch(`${NL_SEARCH_API}/api/health`)).json()
    return Array.isArray(health.engines) ? health.engines : []
  } catch {
    return []
  }
}

/** Start a search and poll until it finishes. Rejects with a user-facing message. */
export async function runAskSearch(
  query: string,
  engine: AskEngine,
  onProgress: (progress: AskProgress) => void,
  signal: AbortSignal,
): Promise<AskResult[]> {
  let job = await readJob(
    await fetch(`${NL_SEARCH_API}/api/nl-search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, engine }),
      signal,
    }),
  )
  while (job.status === 'queued' || job.status === 'running') {
    onProgress({ status: job.status, queuePosition: job.queue_position ?? 0 })
    await wait(POLL_MS, signal)
    job = await readJob(await fetch(`${NL_SEARCH_API}/api/nl-search/${job.job_id}`, { signal }))
  }
  if (job.status === 'error') throw new Error(job.error ?? 'Search failed — please try again.')
  return job.results ?? []
}
