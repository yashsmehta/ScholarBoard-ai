#!/usr/bin/env python3

from __future__ import annotations

import sys

from scholar_board.personas import build


def main() -> int:
    result = build.build_personas()
    summary = result.topup_summary
    lines = [
        f"{result.target_subfield} researchers found: {result.candidates_count}",
        f"Dedup dropped: {result.dedup_dropped}",
        "First/last-author filter: "
        f"kept {result.first_last_kept} of {result.first_last_total}, "
        f"dropped {result.first_last_dropped} (zero matching papers)",
        f"Top-100 score range: {result.score_min:.4f}..{result.score_max:.4f}",
        f"Files written: {result.files_written}",
        "Output directory: personas/",
        "=== Top-up summary ===",
        f"Scholars under {summary.min_papers} papers (before): {summary.under_before}",
        f"Top-up attempted: {summary.attempted}",
        "Could not disambiguate OpenAlex author: "
        f"{summary.disambiguation_failed}",
        f"Reached >={summary.min_papers} papers: {summary.reached_min}",
    ]
    still_under = ", ".join(summary.under_after)
    lines.append(
        f"Still under {summary.min_papers} papers (final): {len(summary.under_after)}"
        f"  (these scholars: {still_under})"
    )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
