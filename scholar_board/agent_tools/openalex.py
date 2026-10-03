#!/usr/bin/env python3
"""OpenAlex helpers for the profile agent (stdlib only).

  python3 tools/openalex.py authors "Leila Wehbe"
      candidate author profiles: id, works, citations, h-index, institutions, top topics
  python3 tools/openalex.py works A123,A456 [--since 2023-01-01] [--all]
      every work since the date, with the PI's exact author position, type, venue,
      citations and citations/year, plus flags (abstract venue, erratum, preprint with
      a published twin). First/last-author works only unless --all.
  python3 tools/openalex.py abstract <doi or W-id>
      reconstructed abstract + full author list
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

UA = {"User-Agent": "ScholarBoard-profile-agent (mailto:scholarboard@example.org)"}
ABSTRACT_RE = re.compile(r"vision sciences society|\bvss\b|supplement|meeting|abstracts?\b|poster|"
                         r"cognitive computational neuroscience|\bccn\b|cosyne|society for neuroscience|\bsfn\b|ohbm",
                         re.I)


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                sys.exit(f"OpenAlex request failed: {e}")
            time.sleep(2 * (attempt + 1))


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", (t or "").lower()).strip()


def authors(name):
    q = urllib.parse.quote(name)
    res = get(f"https://api.openalex.org/authors?search={q}&per-page=10")["results"]
    for a in res:
        insts = [i["display_name"] for i in (a.get("last_known_institutions") or [])]
        hist = [f'{x["institution"]["display_name"]} {min(x["years"])}-{max(x["years"])}'
                for x in (a.get("affiliations") or [])[:5]]
        topics = [t["display_name"] for t in (a.get("topics") or [])[:4]]
        s = a.get("summary_stats") or {}
        print(f'{a["id"].split("/")[-1]} | {a["display_name"]} | works {a["works_count"]} | cites {a["cited_by_count"]} '
              f'| h {s.get("h_index")} | last: {", ".join(insts)}')
        print(f'    history: {"; ".join(hist)}')
        print(f'    topics: {"; ".join(topics)}')


def works(ids, since, show_all):
    ids = [i.strip() for i in ids.split(",") if i.strip()]
    rows, cursor = [], "*"
    filt = f"author.id:{'|'.join(ids)},from_publication_date:{since}"
    while cursor:
        d = get(f"https://api.openalex.org/works?filter={filt}&per-page=200&cursor={cursor}")
        rows += d["results"]
        cursor = d["meta"].get("next_cursor") if d["results"] else None
    today = date.today()
    published_titles = {norm(w["title"]) for w in rows if w.get("type") not in ("preprint",)}
    out = []
    for w in rows:
        A = w.get("authorships") or []
        pos = [i for i, a in enumerate(A) if (a["author"].get("id") or "").split("/")[-1] in ids]
        if not pos:
            continue
        p = "first" if 0 in pos else "last" if len(A) - 1 in pos else "middle"
        if p == "middle" and not show_all:
            continue
        src = (w.get("primary_location") or {}).get("source") or {}
        venue = src.get("display_name") or ""
        pd = w.get("publication_date") or f'{w.get("publication_year")}-01-01'
        age = max((today - date.fromisoformat(pd)).days / 365.25, 0.25)
        flags = []
        if ABSTRACT_RE.search(venue) or (venue.lower() == "journal of vision"):
            flags.append("ABSTRACT?")
        if w.get("type") in ("erratum", "retraction") or (w["title"] or "").lower().startswith(("corrigendum", "erratum", "correction")):
            flags.append("ERRATUM")
        if w.get("type") == "preprint" and sum(norm(x["title"]) == norm(w["title"]) for x in rows) > 1:
            flags.append("DUPLICATE(preprint of a listed version)")
        elif sum(norm(x["title"]) == norm(w["title"]) for x in rows) > 1:
            flags.append("SAME-TITLE-TWIN")
        corr = any(a.get("is_corresponding") for i, a in enumerate(A) if i in pos)
        out.append((pd, p + ("*" if corr else ""), w.get("type"), w.get("cited_by_count", 0),
                    w.get("cited_by_count", 0) / age, venue, w.get("doi") or w["id"], w["title"], len(A), flags))
    out.sort(reverse=True)
    print(f"{len(out)} works ({'all positions' if show_all else 'first/last author only'}; *=corresponding)")
    print("date | pos | type | cites | cites/yr | venue | doi | n_auth | title | flags")
    for r in out:
        print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]:.1f} | {r[5][:45]} | {r[6]} | {r[8]} | {r[7]} | {' '.join(r[9])}")


def abstract(key):
    if key.startswith("W"):
        w = get(f"https://api.openalex.org/works/{key}")
    else:
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", key)
        w = get(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}")
    inv = w.get("abstract_inverted_index") or {}
    words = sorted((p, t) for t, ps in inv.items() for p in ps)
    src = (w.get("primary_location") or {}).get("source") or {}
    print("title:", w["title"])
    print("date:", w.get("publication_date"), "| type:", w.get("type"), "| venue:", src.get("display_name"),
          "| cites:", w.get("cited_by_count"), "| doi:", w.get("doi"))
    print("authors:", ", ".join(a["author"]["display_name"] for a in w.get("authorships") or []))
    print("abstract:", " ".join(t for _, t in words) or "(none in OpenAlex — use Crossref or the landing page)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "authors":
        authors(" ".join(a[1:]))
    elif a[0] == "works":
        since = a[a.index("--since") + 1] if "--since" in a else "2023-01-01"
        works(a[1], since, "--all" in a)
    elif a[0] == "abstract":
        abstract(a[1])
    else:
        sys.exit(__doc__)
