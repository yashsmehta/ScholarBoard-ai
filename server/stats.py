"""Summarize searches.jsonl: volume over time, visitors, geography, top queries, outcomes, cost.

    python -m server.stats [--file PATH] [--days N] [--top N] [--all-queries]

Runs on the prod server (default file /var/lib/scholarboard/searches.jsonl) or on a local copy.
Entries logged before analytics existed have no visitor/country/outcome; they count as searches
but not as visitors.
"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _bar(n: int, top: int, width: int = 30) -> str:
    return "█" * max(1, round(width * n / top)) if n else ""


def _table(title: str, counter: Counter, top: int) -> None:
    print(f"\n{title}")
    if not counter:
        print("  (none)")
        return
    peak = counter.most_common(1)[0][1]
    for k, n in counter.most_common(top):
        print(f"  {str(k)[:40]:<40} {n:>5}  {_bar(n, peak)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default="/var/lib/scholarboard/searches.jsonl")
    ap.add_argument("--days", type=int, help="only the last N days")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--all-queries", action="store_true", help="list every query with time, visitor and place")
    args = ap.parse_args()

    rows = [json.loads(l) for l in Path(args.file).read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp()
        rows = [r for r in rows if r["ts"] >= cutoff]
    if not rows:
        print("No searches logged.")
        return
    for r in rows:  # legacy rows: infer outcome
        r.setdefault("outcome", "cached" if r.get("cached") else "error" if r.get("error") else "ok")
    ts = lambda r: datetime.fromtimestamp(r["ts"], timezone.utc)
    ran = [r for r in rows if r["outcome"] in ("ok", "cached")]
    ok = [r for r in rows if r["outcome"] == "ok"]
    visitors = {r["visitor"] for r in rows if r.get("visitor")}

    print(f"ScholarBoard Agentic Search — {ts(rows[0]):%Y-%m-%d} to {ts(rows[-1]):%Y-%m-%d} (UTC)")
    print(f"  requests {len(rows)} · answered {len(ran)} · unique visitors {len(visitors)} "
          f"(requests with visitor id: {sum(1 for r in rows if r.get('visitor'))})")
    secs = sorted(r["seconds"] for r in ok if r.get("seconds"))
    if secs:
        print(f"  median latency {secs[len(secs)//2]:.0f}s · API-equivalent cost ${sum(r.get('cost_usd') or 0 for r in ok):.2f}")

    _table("Outcomes", Counter(r["outcome"] for r in rows), args.top)
    _table("Engine (uncached runs)", Counter(r.get("engine") for r in ok), args.top)
    _table("Searches per day", Counter(f"{ts(r):%Y-%m-%d}" for r in ran), 60)
    hours = Counter(f"{ts(r).hour:02d}:00" for r in ran)
    _table("Searches by UTC hour", Counter(dict(sorted(hours.items()))), 24)
    _table("Country", Counter(r.get("country", "?") for r in rows if r.get("visitor")), args.top)
    _table("City", Counter(f"{r.get('city', '?')}, {r.get('country', '?')}" for r in rows if r.get("visitor")), args.top)
    _table("Device", Counter(r.get("device") for r in rows if r.get("visitor")), args.top)
    _table("Referrer", Counter(r.get("referrer") for r in rows if r.get("referrer")), args.top)

    per = defaultdict(list)
    for r in rows:
        if r.get("visitor"):
            per[r["visitor"]].append(r)
    print("\nTop visitors (searches · place · first → last seen)")
    for v, rs in sorted(per.items(), key=lambda kv: -len(kv[1]))[: args.top]:
        place = ", ".join(x for x in (rs[0].get("city"), rs[0].get("country")) if x) or "?"
        print(f"  {v}  {len(rs):>4}  {place:<28} {ts(rs[0]):%m-%d %H:%M} → {ts(rs[-1]):%m-%d %H:%M}")
    if per:
        counts = [len(rs) for rs in per.values()]
        print(f"  repeat visitors (2+ searches): {sum(c > 1 for c in counts)}/{len(counts)}")

    _table("Most common queries", Counter(" ".join(r["query"].lower().split()) for r in ran), args.top)
    if args.all_queries:
        print("\nAll queries")
        for r in rows:
            place = ", ".join(x for x in (r.get("city"), r.get("country")) if x) or "-"
            print(f"  {ts(r):%m-%d %H:%M}  {r.get('visitor', '-'):<12} {place:<24} {r['outcome']:<12} {r['query'][:100]}")


if __name__ == "__main__":
    main()
