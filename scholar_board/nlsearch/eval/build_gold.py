"""Build graded relevance labels for the AI-search test set.

Two stages, both on the local Claude Code subscription (headless `claude -p`):

1. pool  — exhaustive recall pass: for every query, Sonnet grades every index
           line (all 796 PIs) in 15 parallel shard calls; anyone graded >= 1 is
           pooled. Independent of the search methods under test.
2. judge — Opus (high effort) reads the full profiles of every pooled PI (plus
           any PI a method later returns that is not yet judged) and grades
           0-3 with a one-line rationale.

Grades: 3 = ideal (current research squarely on the request, all constraints
met); 2 = strong; 1 = partial / tangential; 0 = not relevant or violates an
explicit constraint (location, exclusion, author of the abstract, seniority).

Writes gold.json and pool.json next to this file (tracked in git):
gold = {qid: {pi_id: {"grade", "why"}}}. Run outputs go to data/pipeline/nlsearch_eval/.

Usage:
    uv run -m scholar_board.nlsearch.eval.build_gold            # pool + judge all
    uv run -m scholar_board.nlsearch.eval.build_gold --judge-extra results.json
"""

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scholar_board.config import PIPELINE_DIR, SEARCH_CORPUS_DIR
from scholar_board.nlsearch.rank import _parse_json_array

EVAL_DIR = PIPELINE_DIR / "nlsearch_eval"
GOLD_PATH = Path(__file__).parent / "gold.json"
POOL_PATH = Path(__file__).parent / "pool.json"
QUERIES = json.loads((Path(__file__).parent / "queries.json").read_text(encoding="utf-8"))

POOL_PROMPT = """You are screening vision-science PIs for relevance to a search request. Be recall-oriented: include anyone who could plausibly be a match.

REQUEST:
<<<
{query}
>>>

Below are {n} PIs, one per line: id | name | institution (country) | h-index | subfields | research card.

{shard}

Return ONLY a JSON array of the plausible matches (omit clear non-matches): [{{"id": "<id>", "grade": <1-3>}}] where 3 = clearly squarely on the request, 2 = likely relevant, 1 = possibly relevant. Ignore location/seniority/exclusion constraints at this stage — judge topic relevance only. Return [] if none."""

JUDGE_PROMPT = """You are an expert in vision science and cognitive neuroscience building a gold-standard relevance judgment for a researcher search engine.

SEARCH REQUEST:
<<<
{query}
>>>

Below are full profiles (bio, current research direction, recent papers) of {n} candidate PIs. Grade EVERY candidate on how well they satisfy the request:

3 = ideal: their current research is squarely on the request (for an abstract: they are expert in its core question AND methods); every explicit constraint is met.
2 = strong: substantial, directly relevant work, but less central or covering only part of the request.
1 = partial: tangential or only loosely related.
0 = not relevant, OR violates an explicit constraint in the request (location, "excluding …", seniority such as early-career — use h-index and bio, or being an author of the abstract under review).

Judge only from the profiles; do not rely on outside knowledge of who is famous. Be strict and consistent: reserve 3 for genuinely ideal matches.

{profiles}

Return ONLY a JSON array with one entry per candidate: [{{"id": "<id>", "grade": <0-3>, "why": "<one short clause>"}}]"""


def claude(prompt: str, model: str, effort: str, timeout: int = 900) -> tuple[str, dict]:
    """Headless Claude Code on the logged-in subscription, no tools. Returns (text, usage)."""
    cmd = ["claude", "-p", "--model", model, "--effort", effort, "--safe-mode", "--tools", "",
           "--output-format", "json"]
    env = {k: v for k, v in __import__("os").environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    proc = subprocess.run(cmd, cwd=EVAL_DIR, env=env, input=prompt, capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout)
    data = json.loads(proc.stdout)
    if data.get("is_error"):
        raise RuntimeError(str(data.get("result"))[:300])
    return data["result"], data.get("usage", {})


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def pool(workers: int = 6) -> dict:
    shards = [p.read_text(encoding="utf-8") for p in sorted((SEARCH_CORPUS_DIR / "index").glob("part-*.txt"))]
    pooled = _load(POOL_PATH)
    jobs = [(q, i, s) for q in QUERIES if q["id"] not in pooled for i, s in enumerate(shards)]

    def run(job):
        q, i, shard = job
        text, _ = claude(POOL_PROMPT.format(query=q["query"], n=shard.count("\n"), shard=shard),
                         "claude-sonnet-5-5", "low")
        return q["id"], [r for r in _parse_json_array(text) if r.get("grade", 0) >= 1]

    found: dict[str, dict] = {}
    with ThreadPoolExecutor(workers) as ex:
        for qid, rows in ex.map(run, jobs):
            for r in rows:
                found.setdefault(qid, {})[str(r["id"])] = max(r["grade"], found.get(qid, {}).get(str(r["id"]), 0))
    pooled.update(found)
    POOL_PATH.write_text(json.dumps(pooled, indent=1), encoding="utf-8")
    for q in QUERIES:
        g = pooled.get(q["id"], {})
        print(f"{q['id']:22s} pooled {len(g):3d}  (grade3 {sum(v == 3 for v in g.values())})")
    return pooled


def judge(ids_by_query: dict[str, set[str]], workers: int = 4, batch: int = 30) -> dict:
    """Grade every not-yet-judged id, `batch` full profiles per Opus call."""
    gold = _load(GOLD_PATH)
    profiles_dir = SEARCH_CORPUS_DIR / "profiles"
    jobs = []
    for q in QUERIES:
        todo = sorted(ids_by_query.get(q["id"], set()) - set(gold.get(q["id"], {})))
        jobs += [(q, todo[i : i + batch]) for i in range(0, len(todo), batch)]

    def run(job):
        q, ids = job
        profs = "\n\n".join(f"### {pid}\n" + (profiles_dir / f"{pid}.json").read_text(encoding="utf-8") for pid in ids)
        for _ in range(2):
            try:
                text, _ = claude(JUDGE_PROMPT.format(query=q["query"], n=len(ids), profiles=profs), "claude-opus-5-5", "high")
                return q["id"], {str(r["id"]): {"grade": int(r["grade"]), "why": r.get("why", "")}
                                 for r in _parse_json_array(text) if str(r.get("id")) in ids}
            except Exception as err:  # retry once
                print("judge retry:", q["id"], err)
        return q["id"], {}

    print(f"judging {sum(len(ids) for _, ids in jobs)} candidates in {len(jobs)} calls")
    with ThreadPoolExecutor(workers) as ex:
        for qid, labels in ex.map(run, jobs):
            gold.setdefault(qid, {}).update(labels)
            GOLD_PATH.write_text(json.dumps(gold, indent=1), encoding="utf-8")
    for q in QUERIES:
        g = gold.get(q["id"], {})
        counts = [sum(v["grade"] == k for v in g.values()) for k in (3, 2, 1, 0)]
        print(f"{q['id']:22s} judged {len(g):3d}  grades 3/2/1/0 = {counts}")
    return gold


def main():
    parser = argparse.ArgumentParser(description="Build AI-search gold labels")
    parser.add_argument("--judge-extra", type=Path, help="results JSON {qid: [ids]} whose unjudged ids get judged")
    args = parser.parse_args()
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    if args.judge_extra:
        extra = json.loads(args.judge_extra.read_text())
        judge({k: set(v) for k, v in extra.items()})
        return
    pooled = pool()
    # Full-profile judging covers pool grades >= 2; anyone a method later surfaces is judged via --judge-extra.
    judge({qid: {pid for pid, g in ids.items() if g >= 2} for qid, ids in pooled.items()})


if __name__ == "__main__":
    main()
