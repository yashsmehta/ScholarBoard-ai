"""Run AI-search strategies over the test set and score them against gold labels.

    # Antigravity runs need the token-logging proxy (see usage_proxy.py) on :8765
    uv run -m scholar_board.nlsearch.eval.run_eval run agy_tiered claude_tiered --rep 1 2 [--parallel 10]
    uv run -m scholar_board.nlsearch.eval.run_eval report

Metrics per method (mean over queries): nDCG@10 with gains 2^grade - 1,
P@10 (share of results graded >= 2), recall of grade-3 PIs within the top 10,
constraint/irrelevance violations (results graded 0), seconds, tokens, cost.
For tiered runs, input tokens are also split by whether the agent applied a
hard filter (in_nf / in_f), so the filter path can't hide a regression on the
common, unfiltered one.
"""

import argparse
import json
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scholar_board.nlsearch.eval import methods
from scholar_board.nlsearch.rank import gemini_cost
from scholar_board.nlsearch.eval.build_gold import EVAL_DIR, QUERIES, judge

RESULTS_DIR = EVAL_DIR / "results"
USAGE_LOG = EVAL_DIR / "agy_usage.jsonl"
PROXY = "http://127.0.0.1:8765"

METHODS = {
    # production: tiered agent session (shortlist 100)
    "agy_tiered": ("tiered", {"engine": "agy"}),
    "claude_tiered": ("tiered", {"engine": "claude"}),
    "agy_tiered_med": ("tiered", {"engine": "agy", "model": "gemini-3.8-flash-medium"}),
    "agy_tiered_s50": ("tiered", {"engine": "agy", "shortlist": 50}),
    "claude_tiered_s50": ("tiered", {"engine": "claude", "shortlist": 50}),
}


def _agy_usage(lines: list[str], tag: str) -> dict:
    inp = cached = out = cost = 0.0
    for line in lines:
        rec = json.loads(line)
        if rec.get("tag") != tag:
            continue
        u = rec["usage"]
        i, c = u.get("promptTokenCount", 0), u.get("cachedContentTokenCount", 0)
        o = u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)
        inp, cached, out = inp + i, cached + c, out + o
        cost += gemini_cost(rec["path"], i, c, o)
    return {"input": int(inp), "cached": int(cached), "output": int(out), "cost": round(cost, 4)}


def run(names: list[str], reps: list[int], only: list[str] | None = None, parallel: int = 1) -> None:
    """Run every (method, repeat, query) not yet saved, `parallel` at a time.
    Each agy run gets its own proxy prefix, so token usage stays per run."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    USAGE_LOG.touch()
    lock = threading.Lock()
    files: dict[Path, dict] = {}
    jobs = []
    for name in names:
        for rep in reps:
            path = RESULTS_DIR / (f"{name}.json" if rep == 1 else f"{name}@{rep}.json")
            files[path] = json.loads(path.read_text()) if path.exists() else {}
            jobs += [(name, rep, path, q) for q in QUERIES
                     if not (only and q["id"] not in only) and q["id"] not in files[path]]
    print(f"{len(jobs)} runs, {parallel} in parallel")

    def one(job) -> None:
        name, rep, path, q = job
        fn_name, kwargs = METHODS[name]
        tag = f"{name}.{rep}.{q['id']}"
        if kwargs["engine"] == "agy":
            kwargs = {**kwargs, "base_url": f"{PROXY}/run/{tag}"}
        t0 = time.time()
        try:
            ranked, trace = getattr(methods, fn_name)(q["query"], **kwargs)
        except Exception as err:  # record the failure, keep going
            print(f"{name}@{rep} {q['id']}: FAILED {err}")
            return
        seconds = round(time.time() - t0, 1)
        if kwargs["engine"] == "agy":
            stats = _agy_usage(USAGE_LOG.read_text().splitlines(), tag)
        else:
            u = trace["usage"]
            stats = {"input": u["input"], "cached": u["cached"], "output": u["output"], "cost": u["cost_usd"]}
        with lock:
            files[path][q["id"]] = {"ids": [r["id"] for r in ranked], "results": ranked, "seconds": seconds,
                                    **stats, "trace": trace}
            path.write_text(json.dumps(files[path], indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{name}@{rep} {q['id']:22s} {seconds:6.1f}s  in {stats['input']:>7,}  out {stats['output']:>6,}  "
              f"${stats['cost']}  shortlist={trace.get('shortlist')} filter={trace.get('filter')}", flush=True)

    with ThreadPoolExecutor(parallel) as pool:
        list(pool.map(one, jobs))


def _ndcg(grades: list[int], ideal: list[int]) -> float:
    dcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(grades))
    idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(sorted(ideal, reverse=True)[:10]))
    return dcg / idcg if idcg else 0.0


def _metrics(res: dict, gold: dict) -> dict | None:
    rows = []
    for q in QUERIES:
        r = res.get(q["id"])
        if not r:
            continue
        g = gold.get(q["id"], {})
        grades = [g.get(pid, {}).get("grade", 0) for pid in r["ids"][:10]]
        g3 = {pid for pid, v in g.items() if v["grade"] == 3}
        rows.append({
            "ndcg": _ndcg(grades, [v["grade"] for v in g.values()]),
            "p10": sum(x >= 2 for x in grades) / 10,
            "g3": len(set(r["ids"][:10]) & g3) / min(10, len(g3)) if g3 else 1.0,
            "viol": sum(x == 0 for x in grades),
            "sec": r["seconds"], "in": r["input"], "out": r["output"], "cost": r["cost"],
            "filtered": bool((r.get("trace") or {}).get("filter")) if "trace" in r else None,
        })
    if not rows:
        return None
    m = {k: sum(x[k] for x in rows) / len(rows) for k in rows[0] if k != "filtered"} | {"n": len(rows)}
    for key, flag in (("in_nf", False), ("in_f", True)):
        xs = [x["in"] for x in rows if x["filtered"] is flag]
        m[key] = sum(xs) / len(xs) if xs else None
    return m


def report() -> None:
    all_results = {f.stem: json.loads(f.read_text()) for f in sorted(RESULTS_DIR.glob("*.json"))}
    # Judge anything a method returned that the pool never surfaced.
    returned: dict[str, set] = {}
    for res in all_results.values():
        for qid, r in res.items():
            returned.setdefault(qid, set()).update(r["ids"])
    gold = judge(returned)
    runs: dict[str, list[dict]] = {}
    for name, res in all_results.items():
        m = _metrics(res, gold)
        if m and m["n"] == len(QUERIES):
            runs.setdefault(name.split("@")[0], []).append(m)
    def mean(xs):
        xs = [x for x in xs if x is not None]
        return sum(xs) / len(xs) if xs else None

    def tok(x):
        return f"{x:9,.0f}" if x is not None else f"{'-':>9s}"

    print(f"\n{'method':18s} {'nDCG@10':>14s} {'P@10':>6s} {'G3rec':>6s} {'viol':>5s} {'sec':>6s} {'in_tok':>9s} "
          f"{'in_nf':>9s} {'in_f':>9s} {'out_tok':>8s} {'cost$':>7s} runs")
    for name, ms in sorted(runs.items(), key=lambda kv: -sum(m["ndcg"] for m in kv[1]) / len(kv[1])):
        avg = {k: mean([m[k] for m in ms]) for k in ms[0]}
        sd = (sum((m["ndcg"] - avg["ndcg"]) ** 2 for m in ms) / (len(ms) - 1)) ** 0.5 if len(ms) > 1 else 0.0
        nd = f"{avg['ndcg']:.3f}" + (f" ±{sd:.3f}" if len(ms) > 1 else "       ")
        print(f"{name:18s} {nd:>14s} {avg['p10']:6.2f} {avg['g3']:6.2f} {avg['viol']:5.2f} {avg['sec']:6.1f} "
              f"{tok(avg['in'])} {tok(avg['in_nf'])} {tok(avg['in_f'])} {avg['out']:8,.0f} {avg['cost']:7.3f} {len(ms):4d}")


def main():
    parser = argparse.ArgumentParser(description="AI-search eval")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("methods", nargs="+", choices=sorted(METHODS))
    r.add_argument("--only", nargs="*", help="query ids")
    r.add_argument("--rep", type=int, nargs="+", default=[1], help="repeat indices (results saved as name@rep)")
    r.add_argument("--parallel", type=int, default=10, help="runs at a time (agy: needs usage_proxy.py on :8765)")
    sub.add_parser("report")
    args = parser.parse_args()
    if args.cmd == "run":
        run(args.methods, args.rep, args.only, args.parallel)
    else:
        report()


if __name__ == "__main__":
    main()
