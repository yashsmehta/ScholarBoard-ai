"""Load source scholar data for persona generation."""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from .config import LOCAL_SCHOLARS_JSON, REMOTE_SCHOLARS_JSON


def load_scholars() -> dict[str, Any]:
    """Load scholars from local build data, falling back to the live site."""
    if LOCAL_SCHOLARS_JSON.exists():
        with LOCAL_SCHOLARS_JSON.open(encoding="utf-8") as f:
            return json.load(f)

    with urllib.request.urlopen(REMOTE_SCHOLARS_JSON, timeout=60) as response:
        return json.load(response)
