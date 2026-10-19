"""Chunk repository managing chunk persistence, pgvector searches, and test fallbacks."""

import math
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.chunk import DocumentChunk
from app.models.document import Document, DocumentStatus


class RetrievedChunk:
    """Standardized retrieved chunk object with similarity score and document metadata."""

    def __init__(
        self,
        chunk_id: uuid.UUID,
        document_id: uuid.UUID,
        collection_id: uuid.UUID,
        chunk_index: int,
        content: str,
        filename: str,
        similarity: float,
        page_number: Optional[int] = None,
        section_title: Optional[str] = None,
        chunk_metadata: Optional[Dict[str, Any]] = None,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.collection_id = collection_id
        self.chunk_index = chunk_index
        self.content = content
        self.filename = filename
        self.similarity = similarity
        self.page_number = page_number
        self.section_title = section_title
        self.chunk_metadata = chunk_metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": str(self.chunk_id),
            "document_id": str(self.document_id),
            "collection_id": str(self.collection_id),
            "chunk_index": self.chunk_index,
            "content": self.content,
            "filename": self.filename,
            "similarity": round(self.similarity, 4),
            "page_number": self.page_number,
            "section_title": self.section_title,
            "chunk_metadata": self.chunk_metadata,
        }


class ChunkRepository:
    """Manages chunk vector storage and semantic similarity retrieval."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_batch(self, chunks: List[DocumentChunk]) -> None:
        """Batch inserts document chunks into the database."""
        if not chunks:
            return
        self.session.add_all(chunks)
        await self.session.flush()

    async def delete_by_document(self, document_id: uuid.UUID) -> int:
        """Removes all chunks belonging to a document (used for rollback/cleanup)."""
        stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def similarity_search(
        self,
        query_embedding: List[float],
        collection_id: uuid.UUID,
        owner_id: uuid.UUID,
        top_k: int = 5,
        threshold: float = 0.30,
    ) -> List[RetrievedChunk]:
        """
        Retrieves top-k most semantically similar chunks.
        Uses native pgvector distance operator in PostgreSQL, or in-memory vector
        similarity for test isolation (SQLite).
        """
        if not settings.is_sqlite:
            return await self._search_postgresql(query_embedding, collection_id, owner_id, top_k, threshold)
        return await self._search_sqlite(query_embedding, collection_id, owner_id, top_k, threshold)

    async def _search_postgresql(
        self,
        query_embedding: List[float],
        collection_id: uuid.UUID,
        owner_id: uuid.UUID,
        top_k: int,
        threshold: float,
    ) -> List[RetrievedChunk]:
        """Executes match_document_chunks SQL function via pgvector."""
        query_str = """
            SELECT
                dc.id,
                dc.document_id,
                dc.collection_id,
                dc.chunk_index,
                dc.content,
                dc.page_number,
                dc.section_title,
                dc.chunk_metadata,
                (1.0 - (dc.embedding <=> :embedding_str::vector)) AS similarity,
                d.filename
            FROM document_chunks dc
            INNER JOIN documents d ON d.id = dc.document_id
            WHERE dc.collection_id = :collection_id
              AND dc.owner_id = :owner_id
              AND d.status = :indexed_status
              AND (1.0 - (dc.embedding <=> :embedding_str::vector)) >= :threshold
            ORDER BY dc.embedding <=> :embedding_str::vector ASC
            LIMIT :match_count;
        """
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        stmt = text(query_str).bindparams(
            embedding_str=embedding_str,
            collection_id=collection_id,
            owner_id=owner_id,
            indexed_status=DocumentStatus.INDEXED.value,
            threshold=threshold,
            match_count=top_k,
        )
        result = await self.session.execute(stmt)
        rows = result.fetchall()

        retrieved: List[RetrievedChunk] = []
        for r in rows:
            retrieved.append(
                RetrievedChunk(
                    chunk_id=r.id,
                    document_id=r.document_id,
                    collection_id=r.collection_id,
                    chunk_index=r.chunk_index,
                    content=r.content,
                    filename=r.filename,
                    similarity=float(r.similarity),
                    page_number=r.page_number,
                    section_title=r.section_title,
                    chunk_metadata=r.chunk_metadata,
                )
            )
        return retrieved

    async def _search_sqlite(
        self,
        query_embedding: List[float],
        collection_id: uuid.UUID,
        owner_id: uuid.UUID,
        top_k: int,
        threshold: float,
    ) -> List[RetrievedChunk]:
        """Fallback cosine similarity search for SQLite test isolation."""
        stmt = (
            select(DocumentChunk, Document.filename)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                DocumentChunk.collection_id == collection_id,
                DocumentChunk.owner_id == owner_id,
                Document.status == DocumentStatus.INDEXED.value,
            )
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        scored_chunks = []
        for chunk, filename in rows:
            if not chunk.embedding:
                continue
            sim = self._cosine_similarity(query_embedding, chunk.embedding)
            if sim >= threshold:
                scored_chunks.append((sim, chunk, filename))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        return [
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                collection_id=chunk.collection_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                filename=filename,
                similarity=float(sim),
                page_number=chunk.page_number,
                section_title=chunk.section_title,
                chunk_metadata=chunk.chunk_metadata,
            )
            for sim, chunk, filename in scored_chunks[:top_k]
        ]

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two vector lists."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)
