"""Document repository handling document records, statuses, and duplicate detection."""

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    """Handles CRUD queries for Document records with owner and collection boundaries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        owner_id: uuid.UUID,
        collection_id: uuid.UUID,
        filename: str,
        content_type: str,
        file_size: int,
        content_hash: str,
    ) -> Document:
        """Creates a document record in PENDING state."""
        doc = Document(
            id=uuid.uuid4(),
            owner_id=owner_id,
            collection_id=collection_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            content_hash=content_hash,
            status=DocumentStatus.PENDING.value,
            chunk_count=0,
        )
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def get_by_id(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> Optional[Document]:
        """Retrieves a document enforcing owner isolation."""
        stmt = select(Document).where(
            Document.id == document_id,
            Document.owner_id == owner_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_unscoped(self, document_id: uuid.UUID) -> Optional[Document]:
        """Internal lookup for workers where document_id is pre-validated."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_content_hash(
        self,
        collection_id: uuid.UUID,
        owner_id: uuid.UUID,
        content_hash: str,
    ) -> Optional[Document]:
        """Checks for existing document with identical content in the same collection."""
        stmt = select(Document).where(
            Document.collection_id == collection_id,
            Document.owner_id == owner_id,
            Document.content_hash == content_hash,
            Document.status != DocumentStatus.FAILED.value,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_collection(
        self,
        collection_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> List[Document]:
        """Lists all documents in collection belonging to owner."""
        stmt = (
            select(Document)
            .where(
                Document.collection_id == collection_id,
                Document.owner_id == owner_id,
            )
            .order_by(Document.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        chunk_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Document]:
        """Updates document status, chunk count, and diagnostic errors."""
        doc = await self.get_by_id_unscoped(document_id)
        if not doc:
            return None

        doc.status = status.value
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        if error_message is not None:
            doc.error_message = error_message
        elif status == DocumentStatus.INDEXED:
            doc.error_message = None  # Clear previous error on successful re-index

        await self.session.flush()
        return doc

    async def delete(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
        """Deletes a document and cascades to chunks in pgvector."""
        doc = await self.get_by_id(document_id, owner_id)
        if not doc:
            return False

        await self.session.delete(doc)
        await self.session.flush()
        return True
