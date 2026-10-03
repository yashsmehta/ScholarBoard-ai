"""ScholarBoard natural-language search API.

Public, unauthenticated endpoint called by the static site on GitHub Pages.
Each search runs a headless coding agent over the PI corpus (30–120 s), so the
API is job-based: POST returns a job id immediately and the client polls.

Engine choice is automatic: a search runs on Claude Code (headless, on a Claude
subscription, which allows only a few concurrent sessions) while fewer than
NL_SEARCH_CLAUDE_SLOTS Claude runs are active, otherwise on Antigravity (Gemini
API). A Claude run that fails is retried once on Antigravity. Every result
reports the engine, seconds, and API cost (for Claude, the price Claude Code
reports for the run, although the subscription pays for it).

Abuse and quota protection (each search spends Gemini API credits):
- one search at a time per IP (a second one is refused while the first runs);
- at most NL_SEARCH_CONCURRENCY agent runs at once, NL_SEARCH_MAX_QUEUE waiting;
- per-IP limit of NL_SEARCH_IP_LIMIT uncached searches per 10 minutes;
- global NL_SEARCH_DAILY_LIMIT uncached searches per UTC day;
- identical queries (normalized) are served from an in-memory cache.

Logs each search (query, engine, latency, cost, filter, result ids; never the IP) to
$NL_SEARCH_DATA_DIR/searches.jsonl.

Run locally:
    uv run --with-requirements server/requirements.txt uvicorn server.app:app --port 8001
"""

import json
import logging
import os
import re
import threading
import time
import uuid
from collections import OrderedDict, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scholar_board.config import SEARCH_CORPUS_DIR
from scholar_board.nlsearch.rank import ENGINES, MAX_QUERY_CHARS, search

logger = logging.getLogger("scholarboard.nlsearch")

CORPUS_DIR = Path(os.getenv("NL_SEARCH_CORPUS_DIR", str(SEARCH_CORPUS_DIR)))
DATA_DIR = Path(os.getenv("NL_SEARCH_DATA_DIR", str(CORPUS_DIR.parent)))
CONCURRENCY = int(os.getenv("NL_SEARCH_CONCURRENCY", "10"))
MAX_QUEUE = int(os.getenv("NL_SEARCH_MAX_QUEUE", "20"))
IP_LIMIT = int(os.getenv("NL_SEARCH_IP_LIMIT", "6"))
IP_WINDOW_S = 600
DAILY_LIMIT = int(os.getenv("NL_SEARCH_DAILY_LIMIT", "300"))
CACHE_SIZE = 500
JOB_TTL_S = 3600
# Engines this deployment has (each needs its CLI + credentials). Claude runs are capped at
# CLAUDE_SLOTS at once (subscription concurrency); overflow goes to Antigravity.
ENABLED_ENGINES = [e for e in os.getenv("NL_SEARCH_ENGINES", "agy,claude").split(",") if e in ENGINES]
CLAUDE_SLOTS = int(os.getenv("NL_SEARCH_CLAUDE_SLOTS", "3"))
ALLOWED_ORIGINS = os.getenv(
    "NL_SEARCH_ALLOWED_ORIGINS",
    "https://yashsmehta.com,https://www.yashsmehta.com,http://localhost:5173",
).split(",")

app = FastAPI(title="ScholarBoard NL search", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

_pool = ThreadPoolExecutor(max_workers=CONCURRENCY)
_lock = threading.Lock()
_jobs: dict[str, dict] = {}
_cache: OrderedDict[str, dict] = OrderedDict()
_ip_hits: dict[str, deque] = defaultdict(deque)
_daily = {"day": "", "count": 0}
_active_ip: dict[str, str] = {}  # ip → its queued/running job id
_claude_active = 0


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=MAX_QUERY_CHARS)


def _corpus_version() -> str:
    """Changes whenever the corpus is rebuilt (atomic dir swap → new mtime)."""
    try:
        return str(CORPUS_DIR.stat().st_mtime_ns)
    except FileNotFoundError:
        return "missing"


def _cache_key(query: str) -> str:
    return f"{_corpus_version()}|" + re.sub(r"\s+", " ", query.strip().lower())


def _log_search(entry: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_DIR / "searches.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as err:
        logger.warning("could not log search: %s", err)


def _prune_jobs(now: float) -> None:
    for jid in [j for j, job in _jobs.items() if now - job["created"] > JOB_TTL_S]:
        del _jobs[jid]


def _check_limits(ip: str, now: float) -> None:
    hits = _ip_hits[ip]
    while hits and now - hits[0] > IP_WINDOW_S:
        hits.popleft()
    if len(hits) >= IP_LIMIT:
        raise HTTPException(429, "Too many searches from your connection — please wait a few minutes.")
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _daily["day"] != day:
        _daily.update(day=day, count=0)
    if _daily["count"] >= DAILY_LIMIT:
        raise HTTPException(429, "Daily search limit reached — please try again tomorrow.")
    if sum(1 for j in _jobs.values() if j["status"] in ("queued", "running")) >= MAX_QUEUE:
        raise HTTPException(503, "Search is busy right now — please try again in a minute.")
    hits.append(now)
    _daily["count"] += 1


def _take_engine() -> str:
    """Claude while a subscription slot is free, else Antigravity."""
    global _claude_active
    with _lock:
        if "claude" in ENABLED_ENGINES and _claude_active < CLAUDE_SLOTS:
            _claude_active += 1
            return "claude"
    return "agy" if "agy" in ENABLED_ENGINES else ENABLED_ENGINES[0]


def _release_engine(engine: str) -> None:
    global _claude_active
    if engine == "claude":
        with _lock:
            _claude_active -= 1


def _run_job(job_id: str, query: str, key: str, ip: str) -> None:
    t0 = time.time()
    engine = _take_engine()
    with _lock:
        _jobs[job_id].update(status="running", started=t0, engine=engine)
    trace: dict = {}
    fallback_from, spent = None, 0.0  # spent: API cost of a failed Claude attempt
    try:
        try:
            results = search(query, top_n=10, corpus_dir=CORPUS_DIR, engine=engine, trace=trace)
        except Exception:
            if engine != "claude" or "agy" not in ENABLED_ENGINES:
                raise
            logger.exception("claude search failed; retrying on agy")
            _release_engine(engine)
            spent = (trace.get("usage") or {}).get("cost_usd") or 0.0
            fallback_from, engine = engine, "agy"
            with _lock:
                _jobs[job_id]["engine"] = engine
            results = search(query, top_n=10, corpus_dir=CORPUS_DIR, engine=engine, trace=trace)
    except Exception as err:  # surfaced to the client as a failed job
        logger.exception("search failed")
        with _lock:
            _jobs[job_id].update(status="error", error="Search failed — please try again.")
            _active_ip.pop(ip, None)
        _log_search({"ts": time.time(), "query": query, "engine": engine, "error": str(err)[:300],
                     "seconds": round(time.time() - t0, 1), **trace})
        return
    finally:
        _release_engine(engine)
    cost = (trace.get("usage") or {}).get("cost_usd")
    payload = {"results": results, "engine": engine, "seconds": round(time.time() - t0, 1),
               "cost_usd": None if cost is None else round(cost + spent, 4)}
    with _lock:
        _jobs[job_id].update(status="done", **payload)
        _active_ip.pop(ip, None)
        _cache[key] = payload
        _cache.move_to_end(key)
        while len(_cache) > CACHE_SIZE:
            _cache.popitem(last=False)
    _log_search({"ts": time.time(), "query": query, "engine": engine, "seconds": payload["seconds"],
                 "cost_usd": payload["cost_usd"], "fallback_from": fallback_from,
                 "ids": [r["id"] for r in results], **{k: v for k, v in trace.items() if k != "engine"}})


def _public(job_id: str, job: dict) -> dict:
    out = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "done":
        out.update(results=job["results"], cached=job.get("cached", False), engine=job.get("engine"),
                   seconds=job.get("seconds"), cost_usd=job.get("cost_usd"))
    elif job["status"] == "error":
        out["error"] = job["error"]
    else:
        ahead = sum(1 for j in _jobs.values()
                    if j["status"] == "queued" and j["created"] < job["created"])
        out.update(queue_position=ahead if job["status"] == "queued" else 0, engine=job.get("engine"),
                   elapsed=round(time.time() - job.get("started", job["created"])))
    return out


@app.post("/api/nl-search")
def create_search(body: SearchRequest, request: Request) -> dict:
    query = body.query.strip()
    if len(query) < 3:
        raise HTTPException(422, "Query is too short.")
    now = time.time()
    ip = request.client.host if request.client else "unknown"
    key = _cache_key(query)
    job_id = uuid.uuid4().hex
    with _lock:
        _prune_jobs(now)
        running = _jobs.get(_active_ip.get(ip, ""))
        if running and running["status"] in ("queued", "running"):
            raise HTTPException(409, "You already have an AI search running — please wait for it to finish.")
        if key in _cache:
            _cache.move_to_end(key)
            _jobs[job_id] = {"status": "done", "created": now, "cached": True, **_cache[key]}
            _log_search({"ts": now, "query": query, "cached": True})
            return _public(job_id, _jobs[job_id])
        _check_limits(ip, now)
        _jobs[job_id] = {"status": "queued", "created": now}
        _active_ip[ip] = job_id
    _pool.submit(_run_job, job_id, query, key, ip)
    return _public(job_id, _jobs[job_id])


@app.get("/api/nl-search/{job_id}")
def get_search(job_id: str) -> dict:
    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "Search not found or expired.")
        return _public(job_id, job)


@app.get("/api/health")
def health() -> dict:
    n = len(list((CORPUS_DIR / "profiles").glob("*.json"))) if CORPUS_DIR.exists() else 0
    if n == 0:
        raise HTTPException(503, "search corpus missing")
    return {"ok": True, "pis": n, "engines": ENABLED_ENGINES}
