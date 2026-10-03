"""Shared Gemini API utilities for ScholarBoard.ai.

Provides a client factory, JSON parsing, image generation and embedding utilities.
Gemini covers the map embeddings (embed), the field-level summaries (field_directions)
and the AI Search keywords (search_cards). Per-PI profiles are built by
the headless Claude Code agent in scholar_board/pipeline/profile_agent.py.
"""

import json
import os
import re

import numpy as np
from google import genai
from google.genai import types

from scholar_board.config import get_gemini_api_key

# Fast/cheap model for bulk text tasks (AI Search keywords).
FLASH_MODEL = "gemini-3.8-flash"

def get_client(timeout_s: float | None = None) -> genai.Client:
    """Create a new Gemini API client. Each thread should call this separately.

    Uses Vertex AI (GCP credits) when GOOGLE_GENAI_USE_VERTEXAI=True is set in the
    environment, along with GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION=global.
    Falls back to AI Studio API key otherwise. `timeout_s` bounds each request, so
    bulk jobs fail a stuck call instead of hanging on it.
    """
    http = {"http_options": types.HttpOptions(timeout=int(timeout_s * 1000))} if timeout_s else {}
    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true":
        return genai.Client(**http)  # uses ADC from `gcloud auth application-default login`
    return genai.Client(api_key=get_gemini_api_key(), **http)


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


def generate_json(
    prompt: str,
    response_schema: dict,
    model: str = FLASH_MODEL,
    client: "genai.Client | None" = None,
) -> dict | list | None:
    """Structured JSON generation (response constrained to `response_schema`); None if empty."""
    client = client or get_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json",
                                           response_schema=response_schema),
    )
    return json.loads(response.text) if response.text else None


def generate_image(
    prompt: str,
    model: str = "gemini-3.1-flash-image",
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
    client: "genai.Client | None" = None,
) -> tuple[bytes | None, str | None]:
    """Generate an image using Gemini's Nano Banana 2 model.

    Args:
        prompt: The image generation prompt.
        model: Model ID (default: gemini-3.1-flash-image).
        aspect_ratio: Aspect ratio — "1:1", "16:9", "4:3", "21:9", etc.
        image_size: Resolution — "512px", "1K", "2K", "4K".
        client: Optional pre-created client.

    Returns:
        Tuple of (image_bytes, text). Either may be None depending on the response.
    """
    if client is None:
        client = get_client()

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            ),
        ),
    )

    image_bytes = None
    text = None
    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
            elif part.text:
                text = part.text.strip()

    return image_bytes, text


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
