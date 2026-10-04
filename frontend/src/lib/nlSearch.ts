/** Client for the natural-language PI search API (server/app.py). */

export interface AskResult {
  id: string
  score: number
  reason: string
}

export type AskEngine = 'agy' | 'claude'

export const ENGINE_LABELS: Record<AskEngine, string> = { agy: 'Antigravity', claude: 'Claude Code' }

interface JobResponse {
  job_id: string
  status: 'queued' | 'running' | 'done' | 'error'
  results?: AskResult[]
  error?: string
  queue_position?: number
  engine?: AskEngine | null
  seconds?: number | null
  cost_usd?: number | null
  cached?: boolean
  expected_seconds?: number | null
  steps?: AskSteps
}

/** What the agent has done so far, from its tools' trace (server/app.py, rank.live_steps). */
export interface AskSteps {
  /** A hard filter (location, institution) was applied; `eligible` PIs remain. */
  filtered: boolean
  eligible: number | null
  /** PIs shortlisted from the index, whose full profiles are now being read and ranked. */
  shortlist: number | null
}

export interface AskProgress {
  status: 'queued' | 'running'
  queuePosition: number
  /** Chosen by the server when the search starts running. */
  engine: AskEngine | null
  /** Median run time of recent searches on this engine. */
  expectedSeconds: number | null
  steps: AskSteps | null
}

/** A finished search: results plus which engine ran it, how long it took, and its API cost. */
export interface AskOutcome {
  results: AskResult[]
  engine: AskEngine | null
  seconds: number | null
  costUsd: number | null
  cached: boolean
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

/** Start a search and poll until it finishes. Rejects with a user-facing message.
 *  The server picks the engine (Claude Code while a slot is free, else Antigravity). */
export async function runAskSearch(
  query: string,
  onProgress: (progress: AskProgress) => void,
  signal: AbortSignal,
): Promise<AskOutcome> {
  let job = await readJob(
    await fetch(`${NL_SEARCH_API}/api/nl-search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
      signal,
    }),
  )
  while (job.status === 'queued' || job.status === 'running') {
    onProgress({
      status: job.status, queuePosition: job.queue_position ?? 0, engine: job.engine ?? null,
      expectedSeconds: job.expected_seconds ?? null, steps: job.steps ?? null,
    })
    await wait(POLL_MS, signal)
    job = await readJob(await fetch(`${NL_SEARCH_API}/api/nl-search/${job.job_id}`, { signal }))
  }
  if (job.status === 'error') throw new Error(job.error ?? 'Search failed — please try again.')
  return {
    results: job.results ?? [],
    engine: job.engine ?? null,
    seconds: job.seconds ?? null,
    costUsd: job.cost_usd ?? null,
    cached: job.cached ?? false,
  }
}
