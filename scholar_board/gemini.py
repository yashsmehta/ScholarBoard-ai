"""Shared Gemini API utilities for ScholarBoard.ai.

Provides a client factory, JSON parsing, grounding source extraction,
and embedding utilities used across pipeline modules.
"""

import json
import os
import re

import numpy as np
from google import genai
from google.genai import types

from scholar_board.config import get_gemini_api_key


def get_client() -> genai.Client:
    """Create a new Gemini API client. Each thread should call this separately.

    Uses Vertex AI (GCP credits) when GOOGLE_GENAI_USE_VERTEXAI=True is set in the
    environment, along with GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION=global.
    Falls back to AI Studio API key otherwise.
    """
    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true":
        return genai.Client()  # uses ADC from `gcloud auth application-default login`
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


def generate_text(
    prompt: str,
    model: str = "gemini-3-flash-preview",
    thinking: bool = False,
    system_instruction: str | None = None,
    client: "genai.Client | None" = None,
) -> str | None:
    """Generate text using a Gemini model.

    Args:
        prompt: The prompt to send.
        model: Model ID (e.g. "gemini-3-flash-preview", "gemini-3.1-pro-preview").
        thinking: Enable thinking/reasoning (only meaningful for Pro models).
        system_instruction: Optional system instruction.
        client: Optional pre-created client (useful in threaded code).

    Returns:
        The generated text, or None if the response was empty.
    """
    if client is None:
        client = get_client()

    config_kwargs: dict = {}
    if thinking:
        config_kwargs["thinking_config"] = types.ThinkingConfig(include_thoughts=True)
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction

    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    if response.text is None:
        return None
    return response.text.strip()


def generate_image(
    prompt: str,
    model: str = "gemini-3.1-flash-image-preview",
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
    client: "genai.Client | None" = None,
) -> tuple[bytes | None, str | None]:
    """Generate an image using Gemini's Nano Banana 2 model.

    Args:
        prompt: The image generation prompt.
        model: Model ID (default: gemini-3.1-flash-image-preview).
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
