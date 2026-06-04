"""Embedder interface with a hosted impl (OpenAI) and a deterministic offline fallback.

The hashing fallback keeps the stress suite and Look-Alike hermetic in CI (no API, no network).
Switch to the hosted model by setting OPENAI_API_KEY; nothing else changes.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from cadence.config import Settings

DIM = 1536
_TOKEN = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Deterministic signed feature-hashing into DIM dims, L2-normalized. Lexical-overlap cosine."""

    dim = DIM

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t or "") for t in texts]

    def _one(self, text: str) -> list[float]:
        vec = [0.0] * DIM
        for tok in _TOKEN.findall(text.lower()):
            digest = hashlib.blake2b(tok.encode(), digest_size=8).digest()
            h = int.from_bytes(digest, "big")
            vec[h % DIM] += 1.0 if (h >> 17) & 1 else -1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class OpenAIEmbedder:
    dim = DIM

    def __init__(
        self, api_key: str, model: str = "text-embedding-3-small", base_url: str | None = None
    ) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(
            input=texts, model=self._model, dimensions=DIM, encoding_format="float"
        )
        return [d.embedding for d in resp.data]


def get_embedder(settings: Settings) -> Embedder:
    if settings.openai_api_key:
        return OpenAIEmbedder(
            settings.openai_api_key, settings.embedding_model, settings.openai_base_url
        )
    return HashingEmbedder()


def to_pgvector(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
