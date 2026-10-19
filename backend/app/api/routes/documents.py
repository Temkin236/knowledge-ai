"""Documents API endpoints for upload, indexing status, retry, and deletion."""

import re
import uuid
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.dependencies import CurrentUser, DBSession
from app.models.document import DocumentStatus
from app.repositories.collection_repository import CollectionRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.common import DocumentResponse, DocumentStatusResponse
from app.services.ingestion.pipeline import IngestionPipeline
from app.workers.ingestion_worker import ingestion_worker

router = APIRouter(tags=["Documents"])


def sanitize_filename(filename: str) -> str:
    """Removes path traversal components and unsafe characters from filenames."""
    # Strip directory paths
    clean = filename.replace("\\", "/").split("/")[-1]
    # Remove control characters
    clean = re.sub(r"[\x00-\x1f\x7f]", "", clean)
    return clean or "document"


@router.post(
    "/collections/{collection_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    collection_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    session: DBSession = None,
):
    """
    Upload a document (PDF, DOCX, TXT, MD) to a collection.
    Triggers asynchronous background text extraction, chunking, and embedding.
    """
    col_repo = CollectionRepository(session)
    col = await col_repo.get_by_id(collection_id, current_user.id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

    filename = sanitize_filename(file.filename or "uploaded_file")
    file_bytes = await file.read()

    pipeline = IngestionPipeline(session)
    try:
        doc, is_duplicate = await pipeline.register_document(
            owner_id=current_user.id,
            collection_id=collection_id,
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            file_bytes=file_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # If document was not an already-indexed duplicate, dispatch background worker
    if not is_duplicate or doc.status != DocumentStatus.INDEXED.value:
        ingestion_worker.submit_ingestion_job(
            document_id=doc.id,
            file_bytes=file_bytes,
            filename=filename,
        )

    return doc


@router.get(
    "/collections/{collection_id}/documents",
    response_model=List[DocumentResponse],
)
async def list_documents(
    collection_id: uuid.UUID,
    current_user: CurrentUser,
    session: DBSession,
):
    """List all documents inside a collection with processing statuses."""
    col_repo = CollectionRepository(session)
    col = await col_repo.get_by_id(collection_id, current_user.id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

    doc_repo = DocumentRepository(session)
    return await doc_repo.list_by_collection(collection_id, current_user.id)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    session: DBSession,
):
    """Get document details by ID."""
    doc_repo = DocumentRepository(session)
    doc = await doc_repo.get_by_id(document_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return doc


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    session: DBSession,
):
    """Poll document indexing status and diagnostic error messages."""
    doc_repo = DocumentRepository(session)
    doc = await doc_repo.get_by_id(document_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return DocumentStatusResponse(
        id=doc.id,
        status=doc.status,
        chunk_count=doc.chunk_count,
        error_message=doc.error_message,
        updated_at=doc.updated_at,
    )


@router.post("/documents/{document_id}/retry", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_document_ingestion(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    session: DBSession,
):
    """Retry indexing for a document in FAILED state."""
    doc_repo = DocumentRepository(session)
    doc = await doc_repo.get_by_id(document_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if doc.status != DocumentStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry document in status '{doc.status}'. Retry is only available for FAILED documents.",
        )

    # Reset status to PENDING
    await doc_repo.update_status(document_id, DocumentStatus.PENDING, error_message=None)
    return doc


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    session: DBSession,
):
    """Delete a document and immediately cascade-delete its chunks and vector embeddings."""
    doc_repo = DocumentRepository(session)
    deleted = await doc_repo.delete(document_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return None
