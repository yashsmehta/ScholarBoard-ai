"""Persist / resume scholar contact emails.

Emails are fetched by Claude Code Haiku sub-agents (no API cost, no Gemini/
Vertex involved) and handed to this script, which is the deterministic,
resumable persistence layer:

  * artifact  data/pipeline/scholar_emails.json   (git-ignored → private)
  * DB        scholars.email / email_confidence / email_source_url /
              email_checked_at   (via scholar_board.db.upsert_email)

Emails are intentionally NOT written to data/build/scholars.json — they never
ship to the public frontend.

Usage:
  uv run scripts/apply_emails.py --status
      Show found / not-found / remaining counts.

  uv run scripts/apply_emails.py --todo 20
      Print the next N PIs (is_pi=1) with no email record yet, as JSON —
      the work-list to hand to the Haiku fetchers.

  uv run scripts/apply_emails.py --add '<json>'
      Merge one or more fetched records into the artifact AND the DB.
      Accepts a single record object or a JSON array of records. Each record:
      {"id": "0001", "email": "x@y.edu"|null, "confidence": "high|medium|low",
       "source_url": "...", "reasoning": "..."}

  uv run scripts/apply_emails.py --apply
      Re-upsert the entire artifact into the DB (rebuild the columns).
"""

import argparse
import json
from datetime import date

from scholar_board.config import PIPELINE_DIR
from scholar_board.db import get_connection, init_db, load_scholars, upsert_email

EMAILS_PATH = PIPELINE_DIR / "scholar_emails.json"


def load_artifact() -> dict:
    if EMAILS_PATH.exists():
        return json.loads(EMAILS_PATH.read_text())
    return {}


def save_artifact(data: dict) -> None:
    EMAILS_PATH.parent.mkdir(parents=True, exist_ok=True)
    EMAILS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def apply_to_db(records: dict) -> None:
    conn = get_connection()
    init_db(conn)
    for sid, rec in records.items():
        upsert_email(
            conn,
            sid,
            rec.get("email"),
            confidence=rec.get("confidence"),
            source_url=rec.get("source_url"),
            checked_at=rec.get("checked_at"),
        )
    conn.close()


def cmd_add(blob: str) -> None:
    _add_records(json.loads(blob))


def _add_records(parsed) -> None:
    recs = parsed if isinstance(parsed, list) else [parsed]
    art = load_artifact()
    today = date.today().isoformat()
    pi_names = {s["scholar_id"]: s["scholar_name"] for s in load_scholars(is_pi_only=True)}
    added = {}
    for r in recs:
        sid = str(r["id"]).zfill(4) if str(r["id"]).isdigit() else str(r["id"])
        email = r.get("email") or None
        entry = {
            "name": r.get("name") or pi_names.get(sid, ""),
            "email": email,
            "confidence": r.get("confidence") if email else (r.get("confidence") or "none"),
            "source_url": r.get("source_url"),
            "reasoning": r.get("reasoning"),
            "checked_at": today,
        }
        art[sid] = entry
        added[sid] = entry
    save_artifact(art)
    apply_to_db(added)
    print(f"added/updated {len(added)} record(s); artifact now holds {len(art)}")


def cmd_todo(n: int) -> None:
    art = load_artifact()
    pis = load_scholars(is_pi_only=True)
    todo = [s for s in pis if s["scholar_id"] not in art]
    # enrich with department + lab_url from DB
    conn = get_connection()
    rows = {
        r["id"]: r
        for r in conn.execute(
            "SELECT id, department, lab_url, scholar_profile_url FROM scholars"
        )
    }
    conn.close()
    out = []
    for s in todo[:n]:
        sid = s["scholar_id"]
        row = rows.get(sid, {})
        out.append({
            "id": sid,
            "name": s["scholar_name"],
            "institution": s.get("scholar_institution", ""),
            "department": row["department"] if row else None,
            "lab_url": row["lab_url"] if row else None,
            "scholar_profile_url": row["scholar_profile_url"] if row else None,
        })
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_status() -> None:
    art = load_artifact()
    pis = load_scholars(is_pi_only=True)
    total = len(pis)
    checked = len(art)
    found = sum(1 for r in art.values() if r.get("email"))
    not_found = checked - found
    print(f"PIs total:        {total}")
    print(f"  checked:        {checked}")
    print(f"    with email:   {found}")
    print(f"    no email:     {not_found}")
    print(f"  remaining:      {total - checked}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--todo", type=int, metavar="N")
    ap.add_argument("--add", type=str, metavar="JSON")
    ap.add_argument("--add-file", type=str, metavar="PATH")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.add:
        cmd_add(args.add)
    elif args.add_file:
        _add_records(json.loads(open(args.add_file).read()))
    elif args.todo:
        cmd_todo(args.todo)
    elif args.apply:
        apply_to_db(load_artifact())
        print("re-applied artifact to DB")
    else:
        cmd_status()


if __name__ == "__main__":
    main()
