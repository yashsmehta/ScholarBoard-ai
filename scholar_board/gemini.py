"""Shared Gemini API utilities for ScholarBoard.ai.

Provides a client factory, JSON parsing, grounding source extraction,
and embedding utilities used across pipeline modules.
"""

import json
import re

import numpy as np
from google import genai
from google.genai import types

from scholar_board.config import get_gemini_api_key


def get_client() -> genai.Client:
    """Create a new Gemini API client. Each thread should call this separately."""
    return genai.Client(api_key=get_gemini_api_key())


def parse_json_response(text: str) -> dict | list:
    """Parse JSON from a Gemini response, stripping markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract a JSON object from surrounding text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())

    raise json.JSONDecodeError("No JSON found in response", text, 0)


def extract_grounding_sources(response) -> list[dict]:
    """Extract grounding metadata (source titles + URLs) from a Gemini response."""
    sources = []
    if not response.candidates:
        return sources
    candidate = response.candidates[0]
    if candidate.grounding_metadata:
        meta = candidate.grounding_metadata
        if meta.grounding_chunks:
            for chunk in meta.grounding_chunks:
                if chunk.web:
                    sources.append(
                        {"title": chunk.web.title, "url": chunk.web.uri}
                    )
    return sources


def embed_texts(
    texts: list[str],
    task_type: str = "CLUSTERING",
    model: str = "gemini-embedding-001",
    dim: int = 3072,
    batch_size: int = 100,
) -> np.ndarray:
    """Embed a list of texts using the Gemini embedding API.

    Args:
        texts: Texts to embed.
        task_type: Gemini task type — "CLUSTERING" or "SEMANTIC_SIMILARITY".
        model: Embedding model ID.
        dim: Output dimensionality.
        batch_size: Number of texts per API call.

    Returns:
        NumPy array of shape (len(texts), dim).
    """
    client = get_client()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        print(f"    Batch {i // batch_size + 1} ({len(batch)} texts)...")
        response = client.models.embed_content(
            model=model,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=dim,
            ),
        )
        all_embeddings.extend([e.values for e in response.embeddings])

    return np.array(all_embeddings)
