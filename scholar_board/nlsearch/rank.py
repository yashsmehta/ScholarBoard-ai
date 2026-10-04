"""Natural-language PI search: one headless agent session works through the
corpus in tiers, so it only reads what the request needs (prompt:
nl_search_tiered.md, corpus layout: corpus.py):

  0. hard filter, only when the request explicitly restricts eligibility by
     something meta.db records (location, institution, …): the agent turns it
     into SQL with its own knowledge (tools/sql.py → tools/filter.py);
     most requests skip this and never touch meta.db,
  1. read the whole index (or the filtered part): one technical sentence per
     PI, no metadata → shortlist up to SHORTLIST PIs,
  2. one tools/details.py call → read research summaries + paper titles for
     the shortlist,
  3. rank → top N with reasons.

Engines (both real agent harnesses, same prompt and tools):
- "agy":    Antigravity CLI with a Gemini API key (GEMINI_API_KEY, falling back
            to GOOGLE_API_KEY), in a dedicated HOME (NL_SEARCH_AGY_HOME) so its
            settings never touch a personal login. All tool permissions are
            auto-approved; on the server, the systemd sandbox contains it.
- "claude": headless Claude Code (Sonnet, --safe-mode) with only Read and the
            three `python3 tools/…` commands allowed, on a Claude subscription
            only: API keys are stripped from its environment so it never bills
            the API.

Each search runs in a fresh temporary workspace holding a copy of index/,
tools/ and meta.db; the tools write their output to work/ there, plus a trace
(filters applied, shortlist size) returned to the caller for logging.

Usage:
    uv run -m scholar_board.nlsearch.rank "labs using MEG to study scene perception"
    uv run -m scholar_board.nlsearch.rank --file abstract.txt --engine claude
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from scholar_board.config import DATA_DIR, SEARCH_CORPUS_DIR
from scholar_board.nlsearch.corpus import corpus_ids
from scholar_board.prompt_loader import load_prompt

ENGINES = ("agy", "claude")
AGY_HOME = Path(os.getenv("NL_SEARCH_AGY_HOME", str(DATA_DIR / "agy_home")))
AGY_MODEL = os.getenv("NL_SEARCH_AGY_MODEL", "gemini-3.8-flash-medium")  # = high on the eval, half the time
CLAUDE_MODEL = os.getenv("NL_SEARCH_CLAUDE_MODEL", "claude-sonnet-5-5")
CLAUDE_EFFORT = os.getenv("NL_SEARCH_CLAUDE_EFFORT", "medium")
SHORTLIST = int(os.getenv("NL_SEARCH_SHORTLIST", "100"))
CLAUDE_TOOLS = ["Read", *(f"Bash(python3 tools/{t}.py *)" for t in ("sql", "filter", "details"))]
MAX_QUERY_CHARS = 6000
# Each agent run is a ~150 MB process; cap them across concurrent searches.
_slots = threading.BoundedSemaphore(int(os.getenv("NL_SEARCH_AGENT_SLOTS", "12")))


# Gemini API paid-tier prices, $ per 1M tokens: (input, cached input, output incl. thinking), with the
# date each price takes effect. Source: https://ai.google.dev/gemini-api/docs/pricing (checked 2026-10-03).
GEMINI_PRICES = {
    "flash": [("2000-01-01", (0.75, 0.075, 3.75)), ("2027-01-01", (1.50, 0.15, 7.50))],  # gemini-3.8-flash
    "flash-lite": [("2000-01-01", (0.25, 0.025, 1.50))],  # gemini-3.1-flash-lite (agy's background calls)
}


def gemini_cost(model: str, input_tokens: int, cached_tokens: int, output_tokens: int, day: str | None = None) -> float:
    """API cost in $ of Gemini usage; output_tokens includes thinking tokens."""
    day = day or time.strftime("%Y-%m-%d", time.gmtime())
    family = "flash-lite" if "flash-lite" in model else "flash"
    p_in, p_cached, p_out = [prices for start, prices in GEMINI_PRICES[family] if start <= day][-1]
    return ((input_tokens - cached_tokens) * p_in + cached_tokens * p_cached + output_tokens * p_out) / 1e6


class NoAnswer(Exception):
    """The agent answered in prose (e.g. declined an off-topic or malicious request)."""


def _fill(template: str, **fields: object) -> str:
    """Placeholder substitution without str.format() (prompts contain literal JSON braces).
    `query` goes last so text inside it is never treated as a placeholder."""
    for key in sorted(fields, key=lambda k: k == "query"):
        template = template.replace("{" + key + "}", str(fields[key]))
    return template


def _run(cmd: list[str], name: str, cwd: Path, env: dict, timeout: int, stdin: str = "") -> str:
    with _slots:
        try:
            proc = subprocess.run(cmd, cwd=cwd, env=env, input=stdin, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=timeout + 30)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"{name} timed out after {timeout}s") from exc
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(f"{name} failed (exit {proc.returncode}): {(proc.stderr or proc.stdout).strip()[-500:]}")
    return proc.stdout


def _agy(prompt: str, timeout: int, cwd: Path, model: str | None = None, base_url: str | None = None) -> dict:
    """Run agy → {"text", "usage": {input, cached, output, cost_usd}} (cost from GEMINI_PRICES)."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set")
    settings = AGY_HOME / ".gemini" / "antigravity-cli" / "settings.json"
    if not settings.exists():
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps(
            {"modelProvider": "gemini", "enableTelemetry": False, "toolPermission": "always-proceed"}, indent=2))
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": str(AGY_HOME),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "GEMINI_API_KEY": api_key,
        "AGY_CLI_DISABLE_AUTO_UPDATE": "1",
        **{k: v for k, v in os.environ.items() if k == "GOOGLE_GEMINI_BASE_URL"},  # optional API gateway
        **({"GOOGLE_GEMINI_BASE_URL": base_url} if base_url else {}),
    }
    model = model or AGY_MODEL
    cmd = ["agy", "--model", model, "--dangerously-skip-permissions", "--print-timeout", f"{timeout}s",
           "--output-format", "json", "-p", prompt]
    data = json.loads(_run(cmd, "agy", cwd, env, timeout))
    if data.get("status") != "SUCCESS":
        raise RuntimeError(f"agy: {data.get('status')}: {str(data.get('response'))[:300]}")
    u = data.get("usage") or {}
    cached = u.get("cache_read_tokens", 0)
    inp = u.get("input_tokens", 0) + cached  # agy's input_tokens excludes cache reads
    out = u.get("output_tokens", 0) + u.get("thinking_tokens", 0)
    return {"text": data.get("response") or "",
            "usage": {"input": inp, "cached": cached, "output": out, "cost_usd": gemini_cost(model, inp, cached, out)}}


def _claude(prompt: str, timeout: int, cwd: Path) -> dict:
    """Run Claude Code → {"text", "usage": {input, cached, output, cost_usd}}; cost_usd is the API price
    Claude Code reports (total_cost_usd), even though a subscription pays for it."""
    cmd = ["claude", "-p", "--model", CLAUDE_MODEL, "--effort", CLAUDE_EFFORT, "--safe-mode",
           "--tools", "Read,Bash", "--output-format", "json", "--allowedTools", *CLAUDE_TOOLS]
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    data = json.loads(_run(cmd, "claude", cwd, env, timeout, stdin=prompt))
    if data.get("is_error"):
        raise RuntimeError(f"claude: {str(data.get('result'))[:300]}")
    u = data.get("usage") or {}
    cached = u.get("cache_read_input_tokens", 0)
    return {"text": data.get("result") or "",
            "usage": {"input": u.get("input_tokens", 0) + cached + u.get("cache_creation_input_tokens", 0),
                      "cached": cached, "output": u.get("output_tokens", 0),
                      "cost_usd": float(data.get("total_cost_usd") or 0)}}


def _parse_json_array(text: str) -> list:
    m = re.search(r"\[\s*[\{\]]", text)
    end = text.rfind("]")
    if m is None or end < m.start():
        raise NoAnswer(text[:300])
    data = json.loads(text[m.start() : end + 1])
    if not isinstance(data, list):
        raise ValueError("agent output is not a JSON array")
    return data


def _clean(results: list, valid_ids: set[str], top_n: int) -> list[dict]:
    """Keep well-formed rows with real, unique ids; clamp scores; cap at top_n."""
    out, seen = [], set()
    for r in results:
        sid = str(r.get("id", "")).strip() if isinstance(r, dict) else ""
        if sid not in valid_ids or sid in seen:
            continue
        try:
            score = max(0, min(100, round(float(r.get("score", 0)))))
        except (TypeError, ValueError):
            score = 0
        seen.add(sid)
        out.append({"id": sid, "score": score, "reason": str(r.get("reason", "")).strip()[:400]})
    return out[:top_n]


def _retry(fn, attempts: int = 2):
    """Retry malformed output or transient CLI/API failures; a prose answer (NoAnswer) is final."""
    last: Exception | None = None
    for _ in range(attempts):
        try:
            return fn()
        except NoAnswer:
            raise
        except Exception as err:  # noqa: BLE001
            last = err
    raise RuntimeError(f"search failed: {last}") from last


@contextmanager
def _workspace(corpus_dir: Path):
    """Fresh dir with a copy of the agent-facing corpus; tool output goes to its work/."""
    with tempfile.TemporaryDirectory(prefix="nlsearch-") as tmp:
        ws = Path(tmp)
        for name in ("index", "tools"):
            shutil.copytree(corpus_dir / name, ws / name)
        shutil.copy2(corpus_dir / "meta.db", ws / "meta.db")
        yield ws


def _read_trace(ws: Path) -> dict:
    """Summarize the tools' trace: SQL filters applied, eligible count, shortlist size."""
    path = ws / "work" / "trace.jsonl"
    events = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:  # a line still being written (live reads)
                pass
    filters = [e for e in events if e["tool"] == "filter"]
    details = [e for e in events if e["tool"] == "details"]
    return {"filter": filters[-1]["sql"] if filters else None,
            "eligible": filters[-1]["eligible"] if filters else None,
            "shortlist": details[-1]["n"] if details else None,
            "sql": [e["sql"] for e in events if e["tool"] == "sql"]}


def run_agent(query: str, engine: str, corpus_dir: Path, valid: set[str], top_n: int, shortlist: int,
              timeout: int, trace: dict | None = None, agent=None) -> list[dict]:
    """One agent session over a fresh workspace (prompt: nl_search_tiered.md).

    `agent(prompt, timeout, cwd) -> {"text", "usage"}` overrides the engine's CLI call (eval).
    `trace` receives the engine, the tools' trace (filter, shortlist) and usage summed over
    attempts, including cost_usd (the API price, also for Claude on a subscription).
    """
    prompt = _fill(load_prompt("nl_search_tiered"), n_pis=len(valid),
                   n_shards=f"{len(list((corpus_dir / 'index').glob('part-*.txt'))):02d}",
                   top_n=top_n, shortlist=shortlist, query=query)
    agent = agent or (_agy if engine == "agy" else _claude)
    trace = {} if trace is None else trace
    trace.clear()
    trace.update(engine=engine, usage={"input": 0, "cached": 0, "output": 0, "cost_usd": 0.0})

    def attempt() -> list[dict]:
        with _workspace(corpus_dir) as ws:
            trace["workspace"] = ws  # for live_steps() while the agent runs
            try:
                out = agent(prompt, timeout, ws)
                for k, v in out["usage"].items():
                    trace["usage"][k] += v
                return _clean(_parse_json_array(out["text"]), valid, top_n)
            finally:
                trace.pop("workspace", None)
                trace.update(_read_trace(ws))

    try:
        return _retry(attempt)
    except NoAnswer:
        return []
    finally:
        trace["usage"]["cost_usd"] = round(trace["usage"]["cost_usd"], 4)


def live_steps(trace: dict) -> dict:
    """What the agent has done so far in a running search (read from its tools' trace):
    {"filtered", "eligible", "shortlist"}; safe to call from another thread."""
    ws = trace.get("workspace")
    summary = trace if ws is None else _read_trace(ws)
    return {"filtered": summary.get("filter") is not None, "eligible": summary.get("eligible"),
            "shortlist": summary.get("shortlist")}


def search(query: str, engine: str = "agy", top_n: int = 10, corpus_dir: Path = SEARCH_CORPUS_DIR,
           shortlist: int = SHORTLIST, timeout: int = 300, trace: dict | None = None) -> list[dict]:
    """Rank PIs for a natural-language request → [{id, score, reason}], best first.

    [] means no plausible match (including off-topic or refused requests). Pass
    a dict as `trace` to receive what the agent did (filter SQL, shortlist size).
    """
    query = query.strip()
    if engine not in ENGINES:
        raise ValueError(f"unknown engine: {engine}")
    if not query:
        raise ValueError("empty query")
    if len(query) > MAX_QUERY_CHARS:
        raise ValueError(f"query longer than {MAX_QUERY_CHARS} characters")
    corpus_dir = Path(corpus_dir)
    valid = corpus_ids(corpus_dir)
    if not valid or not (corpus_dir / "meta.db").exists():
        raise RuntimeError(f"search corpus missing, empty or outdated: {corpus_dir}")
    return run_agent(query, engine, corpus_dir, valid, top_n, shortlist, timeout, trace)


def main():
    parser = argparse.ArgumentParser(description="Natural-language PI search")
    parser.add_argument("query", nargs="?", help="Request text")
    parser.add_argument("--file", type=Path, help="Read the request from a file (e.g. an abstract)")
    parser.add_argument("--engine", choices=ENGINES, default="agy")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--corpus", type=Path, default=SEARCH_CORPUS_DIR)
    args = parser.parse_args()

    query = args.file.read_text(encoding="utf-8") if args.file else args.query
    if not query:
        parser.error("give a query or --file")

    t0 = time.time()
    trace: dict = {}
    results = search(query, args.engine, args.top, args.corpus, trace=trace)
    print(f"[{args.engine}, {time.time() - t0:.0f}s, ${trace['usage']['cost_usd']:.3f}] filter={trace.get('filter')} "
          f"eligible={trace.get('eligible')} shortlist={trace.get('shortlist')}")
    for i, r in enumerate(results, 1):
        s = json.loads((args.corpus / "profiles" / f"{r['id']}.json").read_text(encoding="utf-8"))
        print(f"{i:2d}. {r['score']:3d}  {s['name']} ({s['institution']})\n      {r['reason']}")


if __name__ == "__main__":
    main()
