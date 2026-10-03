"""Read-only SQL over the PI metadata, for working out a hard filter.

    python3 tools/sql.py "SELECT DISTINCT institution, country FROM pi WHERE country = 'United States'"

Prints tab-separated rows (at most MAX_ROWS). Output larger than one screen of
text (e.g. bios) goes to work/sql-NN.txt files instead, and their paths are printed.
"""

import sys

from _common import log, run_select, write_files

MAX_ROWS = 400
MAX_PRINT = 15_000  # bytes; agent CLIs truncate long command output


def main():
    if len(sys.argv) != 2:
        sys.exit('usage: python3 tools/sql.py "SELECT ..."')
    cols, rows = run_select(sys.argv[1])
    log({"tool": "sql", "sql": sys.argv[1], "rows": len(rows)})
    lines = ["\t".join(cols) + "\n"]
    lines += ["\t".join("" if v is None else " ".join(str(v).split()) for v in row) + "\n" for row in rows[:MAX_ROWS]]
    if len(rows) > MAX_ROWS:
        lines.append(f"... {len(rows) - MAX_ROWS} more rows not shown; narrow the query.\n")
    text = "".join(lines)
    if len(text.encode()) <= MAX_PRINT:
        print(text, end="")
    else:
        print(f"{len(rows)} rows. Read all of: {' '.join(write_files('sql', 'txt', lines))}")


if __name__ == "__main__":
    main()
