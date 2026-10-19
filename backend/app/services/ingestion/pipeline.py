"""End-to-end document ingestion pipeline service."""

import hashlib
import uuid
from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.models.document import Document, DocumentStatus
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.embeddings.provider import embedding_provider
from app.services.ingestion.chunker import DocumentChunker
from app.services.ingestion.extractor import DocumentExtractor


class IngestionPipeline:
    """Orchestrates document extraction, chunking, embedding, and vector persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.chunk_repo = ChunkRepository(session)
        self.chunker = DocumentChunker()

    @staticmethod
    def compute_hash(file_bytes: bytes) -> str:
        """Computes SHA-256 checksum of raw file bytes."""
        return hashlib.sha256(file_bytes).hexdigest()

    async def register_document(
        self,
        owner_id: uuid.UUID,
        collection_id: uuid.UUID,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> Tuple[Document, bool]:
        """
        Validates file metadata, checks duplicate content hash, and creates
        initial Document record in PENDING status.
        Returns (document, is_duplicate).
        """
        file_size = len(file_bytes)
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(
                f"File size ({file_size / (1024 * 1024):.1f}MB) exceeds maximum allowed limit ({settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.1f}MB)."
            )

        content_hash = self.compute_hash(file_bytes)

        # Check for existing document in same collection
        existing = await self.doc_repo.find_by_content_hash(
            collection_id=collection_id,
            owner_id=owner_id,
            content_hash=content_hash,
        )
        if existing and existing.status == DocumentStatus.INDEXED.value:
            logger.info(f"Duplicate document detected for {filename} (hash: {content_hash}). Returning existing record.")
            return existing, True

        # Create new document record
        doc = await self.doc_repo.create(
            owner_id=owner_id,
            collection_id=collection_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            content_hash=content_hash,
        )
        return doc, False

    async def process_document(
        self,
        document_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
    ) -> Document:
        """
        Executes the full ingestion pipeline:
        Extract -> Chunk -> Embed -> Persist Chunks -> Mark INDEXED.
        Safely rolls back and marks FAILED on any error.
        """
        doc = await self.doc_repo.get_by_id_unscoped(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found.")

        try:
            # 1. Extraction
            logger.info(f"Extracting text from document {document_id} ({filename})")
            await self.doc_repo.update_status(document_id, DocumentStatus.EXTRACTING)
            await self.session.commit()

            sections = DocumentExtractor.extract(file_bytes, filename)

            # 2. Chunking
            logger.info(f"Splitting text for document {document_id} into chunks")
            await self.doc_repo.update_status(document_id, DocumentStatus.CHUNKING)
            await self.session.commit()

            chunks = self.chunker.chunk_sections(
                sections=sections,
                document_id=doc.id,
                collection_id=doc.collection_id,
                owner_id=doc.owner_id,
                source_filename=filename,
                content_hash=doc.content_hash,
            )

            if not chunks:
                raise ValueError("No viable chunks generated from extracted text.")

            # 3. Embedding
            logger.info(f"Generating embeddings for {len(chunks)} chunks of document {document_id}")
            await self.doc_repo.update_status(document_id, DocumentStatus.EMBEDDING, chunk_count=len(chunks))
            await self.session.commit()

            chunk_texts = [c.content for c in chunks]
            embeddings = await embedding_provider.embed_batch(chunk_texts)

            # Assign embeddings to chunk models
            for chunk_obj, emb in zip(chunks, embeddings):
                chunk_obj.embedding = emb

            # 4. Vector Persistence
            # First, clean any pre-existing chunks for this document (e.g. from a retry)
            await self.chunk_repo.delete_by_document(doc.id)
            await self.chunk_repo.create_batch(chunks)

            # 5. Mark as INDEXED
            doc = await self.doc_repo.update_status(
                document_id=doc.id,
                status=DocumentStatus.INDEXED,
                chunk_count=len(chunks),
                error_message=None,
            )
            await self.session.commit()
            logger.info(f"Successfully indexed document {document_id} with {len(chunks)} chunks.")
            return doc

        except Exception as exc:
            logger.error(f"Ingestion failed for document {document_id}: {exc}", exc_info=True)
            await self.session.rollback()

            # Clean partial chunks and update status to FAILED
            try:
                await self.chunk_repo.delete_by_document(document_id)
                doc = await self.doc_repo.update_status(
                    document_id=document_id,
                    status=DocumentStatus.FAILED,
                    error_message=str(exc),
                )
                await self.session.commit()
            except Exception as cleanup_exc:
                logger.error(f"Failed to record FAILED status for document {document_id}: {cleanup_exc}")

            raise
