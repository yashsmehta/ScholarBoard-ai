"""AI-search strategies under evaluation.

tiered — production (rank.run_agent): one agent session that hard-filters only
         when the request needs it, reads the one-sentence index, shortlists
         up to `shortlist` PIs, reads their details, and ranks.

Earlier strategies (single agent over the full-card index, map-reduce) were
retired; their saved results stay in results/ for comparison.

Token usage: Claude's comes from its --output-format json (in the trace); agy's
from the logging proxy (see run_eval.py), which also sees agy's background calls.
"""

from pathlib import Path

from scholar_board.config import SEARCH_CORPUS_DIR
from scholar_board.nlsearch import rank
from scholar_board.nlsearch.corpus import corpus_ids


def tiered(query: str, engine: str, shortlist: int = rank.SHORTLIST, model: str | None = None,
           base_url: str | None = None) -> tuple[list[dict], dict]:
    """Thread-safe: the agent call is passed in, not patched into rank. Returns (ranked, trace)."""
    def agy(prompt: str, timeout: int, cwd: Path) -> dict:
        return rank._agy(prompt, timeout, cwd, model=model, base_url=base_url)
    trace: dict = {}
    ranked = rank.run_agent(query.strip(), engine, SEARCH_CORPUS_DIR, corpus_ids(SEARCH_CORPUS_DIR), 10, shortlist,
                            300, trace, agy if engine == "agy" else None)
    return ranked, trace
