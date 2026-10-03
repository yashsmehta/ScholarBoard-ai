"""Apply a hard filter: write the index lines of only the PIs a query selects.

    python3 tools/filter.py "SELECT id FROM pi WHERE country IN ('Germany', 'France')"

The query's first column must be PI ids. Writes work/index-NN.txt (same line
format as index/) and prints how many PIs matched and which files to read.
"""

import sys

from _common import connect, log, run_select, write_files


def main():
    if len(sys.argv) != 2:
        sys.exit('usage: python3 tools/filter.py "SELECT id FROM pi WHERE ..."')
    _, rows = run_select(sys.argv[1])
    ids = sorted({str(r[0]) for r in rows if r})
    lines = dict(connect().execute("SELECT id, index_line FROM pi").fetchall())
    eligible = [lines[i] + "\n" for i in ids if i in lines]
    log({"tool": "filter", "sql": sys.argv[1], "eligible": len(eligible)})
    if not eligible:
        print("0 PIs match. Check the values with tools/sql.py, or relax the filter.")
        return
    paths = write_files("index", "txt", eligible)
    print(f"{len(eligible)} PIs match. Read all of: {' '.join(paths)}")
    if len(eligible) < 10:
        print("Fewer than 10 PIs match: consider relaxing the filter if that is consistent with the request.")


if __name__ == "__main__":
    main()
