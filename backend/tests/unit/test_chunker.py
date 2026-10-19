"""Unit tests for DocumentChunker."""

import uuid

from app.services.ingestion.chunker import DocumentChunker
from app.services.ingestion.extractor import ExtractedSection


def test_chunker_splits_and_preserves_metadata():
    chunker = DocumentChunker(chunk_size_tokens=20, chunk_overlap_tokens=5)
    # Long text exceeding chunk size
    long_text = "This is a sentence. " * 30
    sections = [
        ExtractedSection(content=long_text, page_number=1, section_title="Overview")
    ]

    doc_id = uuid.uuid4()
    col_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    chunks = chunker.chunk_sections(
        sections=sections,
        document_id=doc_id,
        collection_id=col_id,
        owner_id=owner_id,
        source_filename="test_report.pdf",
        content_hash="abc123hash",
    )

    assert len(chunks) > 1
    # Check index ordering
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert chunk.document_id == doc_id
        assert chunk.collection_id == col_id
        assert chunk.owner_id == owner_id
        assert chunk.page_number == 1
        assert chunk.section_title == "Overview"
        assert chunk.chunk_metadata["source_filename"] == "test_report.pdf"
        assert chunk.chunk_metadata["content_hash"] == "abc123hash"
