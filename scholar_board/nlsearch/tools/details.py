"""Write the full research direction and recent paper titles for a shortlist.

    python3 tools/details.py 0001 0005 E107 ...

Writes work/details-NN.md and prints which files to read.
"""

import re
import sys

from _common import connect, log, write_files


def main():
    ids = list(dict.fromkeys(t for a in sys.argv[1:] for t in re.split(r"[\s,]+", a) if t))
    if not ids:
        sys.exit("usage: python3 tools/details.py ID [ID ...]")
    con = connect()
    pis = {r[0]: r[1:] for r in con.execute("SELECT id, name, direction FROM pi")}
    papers: dict[str, list[str]] = {}
    for pid, title, year in con.execute("SELECT pi_id, title, year FROM paper ORDER BY year DESC"):
        papers.setdefault(pid, []).append(f"{title} ({year})")
    blocks, unknown = [], []
    for pid in ids:
        if pid not in pis:
            unknown.append(pid)
            continue
        name, direction = pis[pid]
        titles = "; ".join(papers.get(pid, [])) or "(none)"
        blocks.append(f"### {pid} | {name}\n{direction or '(no summary)'}\nPapers: {titles}\n\n")
    log({"tool": "details", "n": len(blocks)})
    if unknown:
        print(f"Unknown ids (skipped): {' '.join(unknown)}")
    if blocks:
        print(f"{len(blocks)} profiles. Read all of: {' '.join(write_files('details', 'md', blocks))}")


if __name__ == "__main__":
    main()
