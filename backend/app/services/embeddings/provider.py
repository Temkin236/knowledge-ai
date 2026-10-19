"""Gemini embedding service with batching, validation, and test mock fallback."""

import hashlib
import math
import random
import time
from typing import List, Optional

from google import genai

from app.core.config import settings
from app.core.logging import logger


class EmbeddingProvider:
    """Manages embedding generation with Google Gemini text-embedding-004 and offline fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = settings.EMBEDDING_MODEL,
        dimension: int = settings.EMBEDDING_DIMENSION,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        self.dimension = dimension
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    async def embed_query(self, query: str) -> List[float]:
        """Embeds a single query string for semantic search."""
        results = await self.embed_batch([query])
        return results[0]

    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embeds a list of texts in batches.
        Enforces dimension validation and retry logic.
        """
        if not texts:
            return []

        # Use offline mock if credentials are unavailable (for isolated tests)
        if not self.client or not self.api_key:
            logger.info("Using deterministic offline embedding provider (no GEMINI_API_KEY set).")
            return [self._generate_mock_embedding(t) for t in texts]

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = await self._embed_batch_with_retry(batch)
            for emb in embeddings:
                if len(emb) != self.dimension:
                    raise ValueError(
                        f"Embedding dimension mismatch: expected {self.dimension}, got {len(emb)} from model {self.model_name}."
                    )
            all_embeddings.extend(embeddings)

        return all_embeddings

    async def _embed_batch_with_retry(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
        """Invokes Gemini embed_content with exponential backoff on transient errors."""
        delay = 1.0
        for attempt in range(max_retries):
            try:
                # Synchronous SDK call wrapped safely
                response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=texts,
                )
                # response.embeddings is a list of ContentEmbedding objects
                batch_vectors = []
                for item in response.embeddings:
                    batch_vectors.append(list(item.values))
                return batch_vectors
            except Exception as exc:
                err_msg = str(exc)
                logger.warning(
                    f"Gemini embedding attempt {attempt + 1}/{max_retries} failed: {err_msg}"
                )
                if attempt == max_retries - 1:
                    logger.error("Exhausted all retries for Gemini embedding API.")
                    raise RuntimeError(f"Failed to generate embeddings from Gemini API: {exc}")
                time.sleep(delay)
                delay *= 2.0

        return []

    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic, normalized 768-dim vector using character 3-gram feature hashing.
        Captures morphological stems and semantic similarity for isolated test environments.
        """
        import re

        clean_text = re.sub(r"\s+", " ", text.lower().strip())
        vec = [0.0] * self.dimension

        if len(clean_text) < 3:
            return [0.0] * self.dimension

        # Character 3-grams (sub-word hashing)
        for i in range(len(clean_text) - 2):
            gram = clean_text[i : i + 3]
            idx = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16) % self.dimension
            vec[idx] += 1.0

        # Word tokens
        for w in re.findall(r"\w+", clean_text):
            idx = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % self.dimension
            vec[idx] += 2.0

        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0.0:
            return [0.0] * self.dimension
        return [round(x / norm, 6) for x in vec]


# Global embedding service singleton
embedding_provider = EmbeddingProvider()
