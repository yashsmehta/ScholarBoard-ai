"""
Build a PI's full profile with a headless Claude Code agent.

One agent session per PI (Sonnet 5.5, on the Claude subscription — API keys are stripped
from its environment) researches the person on the web and with small exact tools
(OpenAlex, Crossref, Google Scholar; scholar_board/agent_tools/), following
scholar_board/prompts/profile_agent.md:

  identity → current affiliation + lab link + PI status → photo → citation stats →
  candidate papers (2023+, first/last/second-to-last author) → the 5 most impactful recent works →
  bio + AI summary (research direction) → VSS topic areas, country, sex → self-check

It writes everything into one profile.json in its workspace (data/pipeline/agent_runs/).
This module then re-verifies every paper on OpenAlex/Crossref (exists, PI first/last/second-to-last,
2023+, not a meeting abstract), checks the photo, and writes the DB plus the usual JSON
artifacts. New PIs are then embedded and placed on the map with the saved UMAP model
(no refit, every other dot stays put), `build` runs, and their AI Search keywords are
generated (search_cards, Gemini Flash).

Protected PIs (data/source/protected_pis.json — profiles hand-edited at the PI's
request) are never touched. PIs removed by request (is_pi=false in pi_overrides.json)
are never re-added.

Usage:
    uv run -m scholar_board.pipeline.profile_agent --add "Leila Wehbe" --hint "Stanford University"
    uv run -m scholar_board.pipeline.profile_agent --add "A B" --add "C D" --workers 2
    uv run -m scholar_board.pipeline.profile_agent --id E378           # re-run an existing (unprotected) PI
    uv run -m scholar_board.pipeline.profile_agent --pending           # every scholar never profiled (is_pi unset)
    uv run -m scholar_board.pipeline.profile_agent --id E378 --apply data/pipeline/agent_runs/E378_...  # re-apply a saved run
    uv run -m scholar_board.pipeline.profile_agent --add "A B" --dry-run   # show the plan, no agent, no writes
"""

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from PIL import Image
from thefuzz import fuzz

from scholar_board.config import (
    AGENT_RUNS_DIR, DIRECTIONS_DIR, INSTITUTION_COUNTRIES_PATH, PAPERS_DIR, PI_OVERRIDES_PATH, PICS_DIR,
    PROFILES_DIR, PROTECTED_PIS_PATH, SCHOLARS_JSON, SEX_OVERRIDES_PATH, SEX_PATH, SUBFIELDS_DEF_PATH,
    SUBFIELDS_PATH, SUBFIELD_OVERRIDES_PATH,
)
from scholar_board.db import (
    ensure_scholar, get_connection, init_db, set_is_pi, upsert_papers, upsert_profile, upsert_profile_pic,
    upsert_research_direction, upsert_scholar_stats, upsert_sex, upsert_subfields,
)
from scholar_board.prompt_loader import load_prompt
from scholar_board.pipeline import search_cards

TOOLS_DIR = Path(__file__).resolve().parent.parent / "agent_tools"
MODEL = os.getenv("PROFILE_AGENT_MODEL", "claude-sonnet-5-5")
EFFORT = os.getenv("PROFILE_AGENT_EFFORT", "high")
TIMEOUT_S = 2400
PAPERS_SINCE = "2023-01-01"
PIC_MAX_DIM, PIC_QUALITY = 400, 70  # same as the existing profile_pics/
SOCIAL_RE = re.compile(r"twitter\.com|//x\.com|twimg|bsky|mastodon|linkedin|facebook|instagram|researchgate", re.I)
ABSTRACT_RE = re.compile(r"vision sciences society|\bvss\b|supplement|abstracts? book|meeting abstract|cosyne|"
                         r"cognitive computational neuroscience|\bccn\b|society for neuroscience|\bsfn\b|ohbm", re.I)
# VSS abstracts are printed in Journal of Vision meeting issues with large article numbers
# (e.g. 10.1167/jov.24.10.1474); regular JoV articles are numbered 1, 2, 3...
JOV_ABSTRACT_RE = re.compile(r"10\.1167/jov\.\d+\.\d+\.(\d+)", re.I)
UA = {"User-Agent": "ScholarBoard-profile-agent (mailto:scholarboard@example.org)"}
SECONDARY_SCORE = 0.5


# ── inputs ────────────────────────────────────────────────────────────────

def _json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s).strip()


def _safe(name: str) -> str:
    return re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")


def pic_filename(name: str, scholar_id: str) -> str:
    return f"{name.replace(' ', '_').lower()}_{scholar_id}.jpg"


def similar_names(conn, name: str, threshold: int = 85) -> list[tuple[str, str, int]]:
    """Existing scholars whose name looks like `name` (possible duplicates)."""
    out = []
    for sid, other in conn.execute("SELECT id, name FROM scholars"):
        score = fuzz.token_sort_ratio(_norm(name), _norm(other))
        if score >= threshold:
            out.append((sid, other, score))
    return sorted(out, key=lambda r: -r[2])


def next_extra_id(conn) -> str:
    nums = [int(r[0][1:]) for r in conn.execute("SELECT id FROM scholars WHERE id LIKE 'E%'") if r[0][1:].isdigit()]
    return f"E{max(nums, default=0) + 1:03d}"


def subfields_block() -> tuple[str, set[str]]:
    defs = _json(SUBFIELDS_DEF_PATH, [])
    return "\n".join(f"  - **{d['name']}**: {d['description']}" for d in defs), {d["name"] for d in defs}


def render_prompt(name: str, hint: str) -> str:
    block, _ = subfields_block()
    return (load_prompt("profile_agent").replace("{subfields}", block).replace("{today}", date.today().isoformat())
            .replace("{institution_hint}", hint or "unknown").replace("{name}", name))


# ── the agent ─────────────────────────────────────────────────────────────

def run_agent(sid: str, name: str, hint: str) -> Path:
    """One headless Claude Code session in a fresh workspace; returns the workspace."""
    ws = AGENT_RUNS_DIR / f"{sid}_{time.strftime('%Y%m%d-%H%M%S')}"
    ws.mkdir(parents=True)
    shutil.copytree(TOOLS_DIR, ws / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    prompt = render_prompt(name, hint)
    (ws / "prompt.md").write_text(prompt, encoding="utf-8")
    cmd = ["claude", "-p", "--model", MODEL, "--effort", EFFORT, "--safe-mode", "--output-format", "json",
           "--tools", "Bash,Read,Write,WebSearch,WebFetch",
           "--allowedTools", "Bash", "Read", "Write", "WebSearch", "WebFetch"]
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    t0 = time.time()
    print(f"  [{sid}] agent started for {name}")
    try:
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=ws, env=env, timeout=TIMEOUT_S)
        stdout, stderr = p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        stdout, stderr = "", f"timed out after {TIMEOUT_S}s"
    (ws / "stderr.txt").write_text(stderr or "", encoding="utf-8")
    try:
        result = json.loads(stdout)
    except json.JSONDecodeError:
        result = {"raw": stdout[-3000:]}
    result["wall_seconds"] = round(time.time() - t0)
    _save_json(ws / "result.json", result)
    print(f"  [{sid}] agent finished in {result['wall_seconds']}s, {result.get('num_turns')} turns"
          f"{'' if (ws / 'profile.json').exists() else ' — NO profile.json'}")
    return ws


# ── verification ──────────────────────────────────────────────────────────

def _get(url: str):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2 * (attempt + 1))
    return None


def lookup_paper(paper: dict) -> tuple[str, str, str, list[str]] | None:
    """(title, date, venue, authors) from OpenAlex (by DOI, then by title) or Crossref."""
    m = re.search(r"10\.\d{4,9}/[^\s?#]+", paper.get("url") or "")
    if m:
        doi = m.group(0).rstrip(".,)")
        w = _get(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}")
        if w:
            src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
            return w["title"] or "", w.get("publication_date") or "", src, [a["author"]["display_name"] for a in w["authorships"]]
        c = _get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")
        if c:
            c = c["message"]
            parts = (c.get("published") or c.get("issued") or {}).get("date-parts", [[0]])[0]
            return ((c.get("title") or [""])[0], "-".join(map(str, parts)), (c.get("container-title") or [""])[0],
                    [f'{a.get("given", "")} {a.get("family", "")}' for a in c.get("author", [])])
    w = _get(f"https://api.openalex.org/works?search={urllib.parse.quote(paper.get('title', ''))}&per-page=5")
    for r in (w or {}).get("results", []):
        if difflib.SequenceMatcher(None, _norm(r["title"]), _norm(paper.get("title"))).ratio() > 0.9:
            src = ((r.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
            return r["title"], r.get("publication_date") or "", src, [a["author"]["display_name"] for a in r["authorships"]]
    return None


SENIOR_POSITIONS = ("first", "last", "second-to-last")


def _position(pi_name: str, authors: list[str]) -> str:
    surname = _norm(pi_name).split()[-1]
    toks = [_norm(a).split() for a in authors if a.strip()]
    if not toks:
        return "unknown"
    if surname in toks[0]:
        return "first"
    if surname in toks[-1]:
        return "last"
    if len(toks) > 2 and surname in toks[-2]:
        return "second-to-last"  # often co-senior (shared senior authorship)
    return "middle" if any(surname in t for t in toks) else "absent"


def verify_paper(pi_name: str, p: dict) -> tuple[bool, list[str]]:
    """Independent check of one agent-picked paper. Returns (keep, notes)."""
    notes = []
    if str(p.get("year") or "0")[:4] < PAPERS_SINCE[:4]:
        return False, [f"dated {p.get('year')}"]
    if ABSTRACT_RE.search(p.get("venue") or ""):
        return False, [f"meeting-abstract venue ({p.get('venue')})"]
    jov = JOV_ABSTRACT_RE.search(p.get("url") or "")
    if jov and int(jov.group(1)) >= 100:
        return False, ["Journal of Vision meeting abstract (VSS supplement)"]
    rec = lookup_paper(p)
    if rec is None:
        # e.g. OpenReview-only conference papers: fall back to the agent's author list
        pos = _position(pi_name, re.split(r",\s*", p.get("authors") or ""))
        if pos not in SENIOR_POSITIONS:
            return False, [f"not found on OpenAlex/Crossref and PI is {pos} in the listed authors"]
        return True, ["not found on OpenAlex/Crossref (kept on the agent's verification)"]
    title, pub_date, venue, authors = rec
    if difflib.SequenceMatcher(None, _norm(title), _norm(p.get("title"))).ratio() < 0.8:
        return False, [f"DOI resolves to a different title: {title[:80]}"]
    pos = _position(pi_name, authors)
    if pos not in SENIOR_POSITIONS and p.get("author_position") not in ("co-first", "co-last"):
        return False, [f"PI is {pos} author per the record"]
    if pub_date and pub_date[:4] < PAPERS_SINCE[:4]:
        notes.append(f"record date {pub_date} (agent said {p.get('year')})")
    if ABSTRACT_RE.search(venue or ""):
        return False, [f"meeting-abstract venue per the record ({venue})"]
    return True, notes


def validate(profile: dict, pi_name: str, ws: Path) -> tuple[dict, list[str]]:
    """Clean the agent's profile.json; returns (profile, warnings for a human)."""
    warnings = [f"agent flag: {f}" for f in profile.get("flags") or []]
    kept, seen_titles = [], set()
    for p in (profile.get("papers") or [])[:5]:
        if _norm(p.get("title")) in seen_titles:
            warnings.append(f"paper DROPPED: {p.get('title', '')[:70]} — listed twice")
            continue
        seen_titles.add(_norm(p.get("title")))
        ok, notes = verify_paper(pi_name, p)
        if ok:
            p["citations"] = re.sub(r"\D", "", str(p.get("citations") or "0")) or "0"
            kept.append(p)
        warnings += [f"paper {'kept' if ok else 'DROPPED'}: {p.get('title', '')[:70]} — {n}" for n in notes]
    profile["papers"] = kept

    _, names = subfields_block()
    sf = profile.get("subfields") or {}
    primary = sf.get("primary") if sf.get("primary") in names else None
    if not primary:
        warnings.append(f"invalid primary subfield {sf.get('primary')!r} — add one to subfield_overrides.json")
    secondary = [s for s in sf.get("secondary") or [] if s in names and s != primary][:2]
    profile["subfields"] = {"primary": primary, "secondary": secondary}

    photo = profile.get("photo") or {}
    f = ws / (photo.get("file") or "")
    if photo.get("file") and SOCIAL_RE.search(f"{photo.get('source_url')} {photo.get('image_url')}"):
        warnings.append(f"photo DROPPED: social-media source {photo.get('source_url')}")
        photo["file"] = None
    elif photo.get("file") and not f.is_file():
        warnings.append("photo DROPPED: file missing in workspace")
        photo["file"] = None
    elif photo.get("file"):
        with Image.open(f) as img:
            if min(img.size) < 150:
                warnings.append(f"photo is small ({img.size[0]}x{img.size[1]})")
    if not photo.get("file"):
        warnings.append("no photo — the map shows the default avatar")
    profile["photo"] = photo

    if profile.get("sex") not in ("female", "male", "unknown"):
        profile["sex"] = "unknown"
    return profile, warnings


# ── writing ───────────────────────────────────────────────────────────────

def apply_profile(conn, sid: str, name: str, profile: dict, ws: Path) -> bool:
    """Write the validated profile to the DB + JSON artifacts. Returns True if the PI is on the map."""
    safe = _safe(name)
    aff, lab = profile.get("affiliation") or {}, profile.get("lab") or {}
    pi_override = _json(PI_OVERRIDES_PATH, {}).get(sid)
    is_pi = bool((profile.get("is_pi") or {}).get("value")) and bool(profile.get("papers"))
    if pi_override is not None:
        is_pi = bool(pi_override["is_pi"])

    upsert_profile(conn, sid, institution=aff.get("institution"), department=aff.get("department"),
                   lab_name=lab.get("lab_name"), lab_url=lab.get("lab_url"),
                   main_research_area=profile.get("main_research_area"), bio=profile.get("bio"))
    set_is_pi(conn, sid, is_pi)
    _save_json(PROFILES_DIR / f"{sid}_{safe}.json", {
        "scholar_id": sid, "scholar_name": name, "institution": aff.get("institution"),
        "department": aff.get("department"), "lab_name": lab.get("lab_name"), "lab_url": lab.get("lab_url"),
        "main_research_area": profile.get("main_research_area"), "bio": profile.get("bio"),
        "is_pi": is_pi, "source": "profile_agent", "agent_run": ws.name,
        "affiliation": aff, "identity": profile.get("identity"), "is_pi_reason": profile.get("is_pi"),
        "flags": profile.get("flags"),
    })
    if not is_pi:
        return False

    stats = profile.get("scholar_stats") or {}
    to_int = lambda v: int(re.sub(r"\D", "", str(v))) if v is not None and re.sub(r"\D", "", str(v)) else None
    upsert_scholar_stats(conn, sid, to_int(stats.get("total_citations")), to_int(stats.get("h_index")),
                         stats.get("source_url"))

    papers = [{k: p.get(k) for k in ("title", "abstract", "year", "venue", "citations", "authors", "url")}
              for p in profile["papers"]]
    upsert_papers(conn, sid, papers)
    _save_json(PAPERS_DIR / f"{sid}_{safe}.json", {"scholar_id": sid, "scholar_name": name, "papers": papers,
                                                    "source": "profile_agent",
                                                    "excluded_notable": profile.get("excluded_notable")})

    upsert_research_direction(conn, sid, profile.get("research_direction") or "")
    _save_json(DIRECTIONS_DIR / f"{sid}_{safe}.json", {"scholar_id": sid, "scholar_name": name,
                                                        "research_direction": profile.get("research_direction")})

    sf = profile["subfields"]
    override = _json(SUBFIELD_OVERRIDES_PATH, {}).get(sid)
    primary, secondary = (override["primary"], override.get("secondary", [])) if override else (sf["primary"], sf["secondary"])
    if primary:
        tags = [{"subfield": primary, "score": 1.0}] + [{"subfield": s, "score": SECONDARY_SCORE} for s in secondary if s != primary][:2]
        upsert_subfields(conn, sid, primary, tags)
        assignments = _json(SUBFIELDS_PATH, {})
        assignments[sid] = {"primary_subfield": primary, "subfields": tags}
        _save_json(SUBFIELDS_PATH, assignments)

    inst, country = aff.get("institution"), profile.get("country")
    countries = _json(INSTITUTION_COUNTRIES_PATH, {})
    if inst and country and inst not in countries:
        countries[inst] = country
        _save_json(INSTITUTION_COUNTRIES_PATH, dict(sorted(countries.items())))
    elif inst and country and countries.get(inst) != country:
        print(f"  [{sid}] note: institution_countries.json maps {inst!r} to {countries[inst]!r}, agent said {country!r}")

    sex = _json(SEX_OVERRIDES_PATH, {}).get(sid) or profile.get("sex")
    upsert_sex(conn, sid, sex)
    sexes = _json(SEX_PATH, {})
    sexes[sid] = sex
    _save_json(SEX_PATH, dict(sorted(sexes.items())))

    photo = profile.get("photo") or {}
    if photo.get("file"):
        PICS_DIR.mkdir(parents=True, exist_ok=True)
        out = PICS_DIR / pic_filename(name, sid)
        with Image.open(ws / photo["file"]) as img:
            img = img.convert("RGB")
            img.thumbnail((PIC_MAX_DIM, PIC_MAX_DIM))
            img.save(out, "JPEG", quality=PIC_QUALITY, optimize=True)
        upsert_profile_pic(conn, sid, out.name)
    return True


# ── main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build PI profiles with a headless Claude Code agent")
    parser.add_argument("--add", action="append", default=[], help="Name of a new PI (repeatable)")
    parser.add_argument("--hint", action="append", default=[],
                        help="Institution on file for the matching --add (optional, may be outdated)")
    parser.add_argument("--id", action="append", default=[], help="Re-run an existing PI by id (repeatable)")
    parser.add_argument("--pending", action="store_true", help="Profile every scholar in the DB with is_pi unset")
    parser.add_argument("--apply", type=str, default=None, help="Apply a saved agent workspace instead of running the agent (one --id)")
    parser.add_argument("--workers", type=int, default=2, help="Parallel agent sessions")
    parser.add_argument("--allow-similar", action="store_true", help="Add even if a similar name already exists")
    parser.add_argument("--no-place", action="store_true", help="Skip embed/UMAP placement, build and search cards")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = get_connection()
    init_db(conn)
    protected = _json(PROTECTED_PIS_PATH, {})
    removed = {sid for sid, o in _json(PI_OVERRIDES_PATH, {}).items() if not o.get("is_pi", True)}

    targets: list[tuple[str, str, str]] = []  # (id, name, hint)
    for i, name in enumerate(args.add):
        hint = args.hint[i] if i < len(args.hint) else ""
        dupes = similar_names(conn, name)
        blocked = [d for d in dupes if d[0] in removed]
        if blocked:
            sys.exit(f"{name!r} matches {blocked[0][1]} ({blocked[0][0]}), removed from the map at their request — not re-adding.")
        if dupes and not args.allow_similar:
            sys.exit(f"{name!r} looks like an existing scholar: {dupes[:3]}. Use --id to re-run them, or --allow-similar.")
        sid = next_extra_id(conn) if not targets else f"E{int(targets[-1][0][1:]) + 1:03d}"
        targets.append((sid, name, hint))
    for sid in args.id:
        row = conn.execute("SELECT name, institution FROM scholars WHERE id = ?", (sid,)).fetchone()
        if not row:
            sys.exit(f"No scholar with id {sid}")
        if sid in protected:
            sys.exit(f"{sid} {row['name']} is protected ({protected[sid]['reason']}). Edit their data by hand.")
        targets.append((sid, row["name"], row["institution"] or ""))
    if args.pending:
        for row in conn.execute("SELECT id, name, institution FROM scholars WHERE is_pi IS NULL ORDER BY id"):
            if row["id"] not in protected and row["id"] not in removed:
                targets.append((row["id"], row["name"], row["institution"] or ""))
        if not targets:
            print("No pending scholars (every scholar in the DB has been profiled).")
            return
    if not targets:
        parser.error("give --add NAME, --id ID or --pending")

    print(f"Profile agent ({MODEL}, effort {EFFORT}) for {len(targets)} PI(s):")
    for sid, name, hint in targets:
        print(f"  {sid}  {name}  (on file: {hint or '-'})")
    if args.dry_run:
        print(f"\n[DRY RUN] prompt for the first PI:\n\n{render_prompt(targets[0][1], targets[0][2])[:1500]}\n...")
        return

    for sid, name, hint in targets:
        ensure_scholar(conn, sid, name, hint or None)
        conn.execute("UPDATE scholars SET source = COALESCE(source, 'agent') WHERE id = ?", (sid,))
        conn.commit()

    if args.apply:
        workspaces = {targets[0][0]: Path(args.apply)}
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {sid: pool.submit(run_agent, sid, name, hint) for sid, name, hint in targets}
            workspaces = {sid: f.result() for sid, f in futures.items()}

    on_map, report = [], {}
    for sid, name, _ in targets:
        ws = workspaces.get(sid)
        if not ws or not (ws / "profile.json").exists():
            report[sid] = ["FAILED: no profile.json — see " + str(ws)]
            continue
        profile, warnings = validate(json.loads((ws / "profile.json").read_text(encoding="utf-8")), name, ws)
        _save_json(ws / "validated.json", {"profile": profile, "warnings": warnings})
        if apply_profile(conn, sid, name, profile, ws):
            on_map.append(sid)
        else:
            warnings.insert(0, "NOT A PI (or no qualifying papers) — kept in the DB with is_pi = 0, not on the map")
        report[sid] = warnings
    conn.close()

    if on_map and not args.no_place:
        from scholar_board.pipeline.cluster import place_ids
        from scholar_board.pipeline.embed import embed_ids
        print("\nPlacing on the map (saved UMAP model, no refit)...")
        place_ids(embed_ids(on_map))
        subprocess.run([sys.executable, "-m", "scholar_board.pipeline.build"], check=True)
        search_cards.update_cards(on_map)

    print("\n── Review ──")
    for sid, name, _ in targets:
        print(f"\n{sid} {name}{'  (on the map)' if sid in on_map else ''}")
        for w in report.get(sid, []):
            print(f"  - {w}")
    print("\nCheck the photo and profile in the app, then commit data/build/ (and data/source/ JSON changes).")


if __name__ == "__main__":
    main()
