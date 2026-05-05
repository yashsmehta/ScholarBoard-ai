#!/usr/bin/env python3
"""Build markdown personas for top Brain-AI Alignment researchers."""

from __future__ import annotations

import sys

from scholar_board.personas import build


def main() -> int:
    """Run the persona build and print the summary."""
    result = build.build_personas()

    print(f"{result.target_subfield} researchers found: {result.candidates_count}")
    print(f"Dedup dropped: {result.dedup_dropped}")
    print(
        "First/last-author filter: "
        f"kept {result.first_last_kept} of {result.first_last_total}, "
        f"dropped {result.first_last_dropped} (zero matching papers)"
    )
    print(f"Top-100 score range: {result.score_min:.4f}..{result.score_max:.4f}")
    print(f"Files written: {result.files_written}")
    print("Output directory: personas/")
    print("=== Top-up summary ===")
    summary = result.topup_summary
    print(f"Scholars under {summary.min_papers} papers (before): {summary.under_before}")
    print(f"Top-up attempted: {summary.attempted}")
    print(
        "Could not disambiguate OpenAlex author: "
        f"{summary.disambiguation_failed}"
    )
    print(f"Reached >={summary.min_papers} papers: {summary.reached_min}")
    still_under = ", ".join(summary.under_after)
    print(
        f"Still under {summary.min_papers} papers (final): {len(summary.under_after)}"
        f"  (these scholars: {still_under})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
