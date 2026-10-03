#!/usr/bin/env python3
"""Verify a paper on Crossref (stdlib only).

  python3 tools/crossref.py <doi> [<doi> ...]
      title, type, venue, date, full author order for each DOI (or NOT FOUND)
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "ScholarBoard-profile-agent (mailto:scholarboard@example.org)"}


def check(doi):
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi.strip())
    for attempt in range(3):
        try:
            url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                m = json.load(r)["message"]
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"{doi}: NOT FOUND on Crossref (arXiv/OpenReview DOIs may live on DataCite — check the landing page)")
                return
            time.sleep(2 * (attempt + 1))
        except Exception:  # noqa: BLE001
            time.sleep(2 * (attempt + 1))
    else:
        print(f"{doi}: Crossref unreachable")
        return
    parts = (m.get("published") or m.get("issued") or {}).get("date-parts", [[None]])[0]
    authors = [f'{a.get("given", "")} {a.get("family", "")}'.strip() or a.get("name", "") for a in m.get("author", [])]
    print(f"{doi}: {(m.get('title') or [''])[0]}")
    print(f"    type={m.get('type')} | venue={(m.get('container-title') or [''])[0]} | date={'-'.join(map(str, parts))}")
    print(f"    authors ({len(authors)}): {', '.join(authors)}")
    rel = m.get("relation") or {}
    if rel:
        links = ", ".join(k + "->" + str(v[0].get("id")) for k, v in rel.items() if v)
        print(f"    relations: {links}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for d in sys.argv[1:]:
        check(d)
