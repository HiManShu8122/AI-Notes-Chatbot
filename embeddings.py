"""Lightweight embeddings using OpenAI API (zero local model downloads)."""

import hashlib
from typing import List


def get_embedding(text: str, api_key: str) -> List[float]:
    """Return a 1536-dim embedding via OpenAI's text-embedding-3-small."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    resp = client.embeddings.create(model="text-embedding-3-small", input=text.strip())
    return resp.data[0].embedding


def hash_to_vector(text: str, dim: int = 384) -> List[float]:
    """Deterministic pseudo-embedding from text hash. Used as fallback."""
    h = hashlib.sha256(text.encode()).digest()
    vec = []
    for i in range(dim):
        byte_idx = i % len(h)
        val = ((h[byte_idx] << (i % 8)) | (h[(byte_idx + 1) % len(h)] >> (8 - (i % 8)))) & 0xFF
        vec.append((val / 127.5) - 1.0)
    # L2-normalize
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
