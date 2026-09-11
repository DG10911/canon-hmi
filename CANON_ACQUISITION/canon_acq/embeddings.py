"""Deterministic PLACEHOLDER embeddings (spec section 52).

These are hash-projected vectors, NOT semantic embeddings. They keep the
vector-index dataset shape and metadata-filter plumbing exercisable in P0
without pulling in a model. Section 67 forbids fake data; this is why every
embedding row is explicitly tagged method="placeholder-hash" and carries a
note that it must be replaced by a real embedding model in production.
"""
from __future__ import annotations
import hashlib
import struct

DIM = 16


def embed(text: str, dim: int = DIM) -> list:
    """Map text -> deterministic unit-ish vector via SHA-256 stream expansion."""
    vec: list[float] = []
    counter = 0
    while len(vec) < dim:
        h = hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest()
        for i in range(0, len(h), 4):
            (u,) = struct.unpack(">I", h[i:i + 4])
            vec.append((u / 0xFFFFFFFF) * 2.0 - 1.0)  # [-1, 1]
            if len(vec) >= dim:
                break
        counter += 1
    # L2 normalise
    norm = sum(x * x for x in vec) ** 0.5 or 1.0
    return [round(x / norm, 6) for x in vec]
