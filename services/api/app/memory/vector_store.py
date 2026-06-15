"""Vector store for embeddings using in-memory store with optional pgvector backend."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog

logger = structlog.get_logger()


@dataclass
class VectorDocument:
    """A document with its embedding vector."""
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SimpleEmbedder:
    """A lightweight text embedder using TF-IDF-like hashing (no external deps)."""

    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        words = text.lower().split()
        for word in words:
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % self.dim
            vec[idx] += 1.0
        # Normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class VectorStore:
    """In-memory vector store with cosine similarity search."""

    def __init__(self, embedder: SimpleEmbedder | None = None):
        self.embedder = embedder or SimpleEmbedder()
        self._documents: dict[str, VectorDocument] = {}

    async def add(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Add a document to the store."""
        doc = VectorDocument(
            content=content,
            metadata=metadata or {},
            embedding=self.embedder.embed(content),
        )
        self._documents[doc.id] = doc
        logger.debug("vector_add", doc_id=doc.id, total=len(self._documents))
        return doc.id

    async def add_batch(self, documents: list[dict]) -> list[str]:
        """Add multiple documents."""
        ids = []
        for doc in documents:
            doc_id = await self.add(doc.get("content", ""), doc.get("metadata"))
            ids.append(doc_id)
        return ids

    async def search(self, query: str, top_k: int = 5, filter_metadata: dict | None = None) -> list[dict]:
        """Search for similar documents."""
        query_vec = self.embedder.embed(query)
        results = []
        for doc in self._documents.values():
            if filter_metadata:
                if not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue
            score = _cosine_similarity(query_vec, doc.embedding)
            results.append({"id": doc.id, "content": doc.content, "metadata": doc.metadata, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def delete(self, doc_id: str) -> bool:
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False

    @property
    def count(self) -> int:
        return len(self._documents)


# Global instance
vector_store = VectorStore()
