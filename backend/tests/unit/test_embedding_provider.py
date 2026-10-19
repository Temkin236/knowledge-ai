"""Unit tests for EmbeddingProvider validation and fallback."""

import pytest

from app.services.embeddings.provider import EmbeddingProvider


@pytest.mark.asyncio
async def test_mock_embedding_generation():
    provider = EmbeddingProvider(api_key=None, dimension=768)
    query = "What is Retrieval-Augmented Generation?"
    vector = await provider.embed_query(query)

    assert len(vector) == 768
    # Assert deterministic output
    vector2 = await provider.embed_query(query)
    assert vector == vector2

    # Different text should yield different vector
    other_vector = await provider.embed_query("Completely different topic.")
    assert vector != other_vector


@pytest.mark.asyncio
async def test_batch_embedding_generation():
    provider = EmbeddingProvider(api_key=None, dimension=768)
    texts = ["Paragraph 1", "Paragraph 2", "Paragraph 3"]
    vectors = await provider.embed_batch(texts, batch_size=2)

    assert len(vectors) == 3
    for v in vectors:
        assert len(v) == 768
