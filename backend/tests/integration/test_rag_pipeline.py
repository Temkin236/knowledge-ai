"""Integration tests for the complete end-to-end RAG pipeline and grounding behavior."""

import os
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk
from app.models.document import DocumentStatus
from app.rag.prompts import FALLBACK_INSUFFICIENT_EVIDENCE
from app.repositories.collection_repository import CollectionRepository
from app.services.ingestion.pipeline import IngestionPipeline


@pytest.mark.asyncio
async def test_full_rag_pipeline_with_grounded_answer_and_abstention(
    client: AsyncClient,
    test_db_session: AsyncSession,
    user_a_token: str,
    user_b_token: str,
):
    headers_a = {"Authorization": f"Bearer {user_a_token}"}
    headers_b = {"Authorization": f"Bearer {user_b_token}"}

    # 1. User A creates a collection
    col_repo = CollectionRepository(test_db_session)
    col = await col_repo.create(
        owner_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Quantum Research 2026",
        description="Helios Labs quantum processor disclosures",
    )
    await test_db_session.commit()

    # 2. Read fixture document
    fixture_path = os.path.join(
        os.path.dirname(__file__), "../fixtures/quantum_computing_report.md"
    )
    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    # 3. Ingest document synchronously via IngestionPipeline into test DB
    pipeline = IngestionPipeline(test_db_session)
    doc, _ = await pipeline.register_document(
        owner_id=col.owner_id,
        collection_id=col.id,
        filename="quantum_computing_report.md",
        content_type="text/markdown",
        file_bytes=file_bytes,
    )
    await test_db_session.commit()

    indexed_doc = await pipeline.process_document(
        document_id=doc.id,
        file_bytes=file_bytes,
        filename="quantum_computing_report.md",
    )

    assert indexed_doc.status == DocumentStatus.INDEXED.value
    assert indexed_doc.chunk_count > 0

    # Verify chunks exist in DB
    chunk_check = await test_db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    chunks_in_db = chunk_check.scalars().all()
    assert len(chunks_in_db) == indexed_doc.chunk_count

    # 4. Query KNOWN FACT present in document
    known_question = "What was the error threshold and number of qubits in the Aurora-7 processor?"
    chat_resp = await client.post(
        "/api/v1/chat",
        json={"collection_id": str(col.id), "message": known_question},
        headers=headers_a,
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()

    assert chat_data["conversation_id"] is not None
    assert chat_data["answer"] != FALLBACK_INSUFFICIENT_EVIDENCE
    assert "qubit" in chat_data["answer"].lower() or "error" in chat_data["answer"].lower() or "aurora" in chat_data["answer"].lower()
    # Citations must be present and verified against the fixture file
    assert len(chat_data["citations"]) >= 1
    assert chat_data["citations"][0]["filename"] == "quantum_computing_report.md"
    assert chat_data["retrieval_metadata"]["evidence_sufficient"] is True

    # 5. Query ABSENT FACT NOT present in document
    absent_question = "What was the CEO's favorite breakfast cereal and shoe size?"
    absent_resp = await client.post(
        "/api/v1/chat",
        json={"collection_id": str(col.id), "message": absent_question},
        headers=headers_a,
    )
    assert absent_resp.status_code == 200
    absent_data = absent_resp.json()

    # Grounding rule: System must state fallback and NEVER invent citations or facts
    assert absent_data["answer"] == FALLBACK_INSUFFICIENT_EVIDENCE
    assert len(absent_data["citations"]) == 0

    # 6. Cross-User Isolation: User B cannot chat with User A's collection
    cross_resp = await client.post(
        "/api/v1/chat",
        json={"collection_id": str(col.id), "message": known_question},
        headers=headers_b,
    )
    assert cross_resp.status_code == 404

    # 7. Document Deletion cascades to chunks
    del_resp = await client.delete(f"/api/v1/documents/{doc.id}", headers=headers_a)
    assert del_resp.status_code == 204

    # Verify chunks are removed from database
    chunk_check_after = await test_db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    assert len(chunk_check_after.scalars().all()) == 0
