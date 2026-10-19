"""Unit tests for LangGraph RAG workflow nodes and citation validation."""

import pytest

from app.rag.nodes import (
    evaluate_evidence_node,
    validate_and_prepare_query_node,
    validate_citations_node,
)


@pytest.mark.asyncio
async def test_validate_and_prepare_query():
    state = {"query": "  What are the operating margins?  "}
    result = await validate_and_prepare_query_node(state)
    assert result["query"] == "What are the operating margins?"

    with pytest.raises(ValueError, match="empty"):
        await validate_and_prepare_query_node({"query": "   "})


@pytest.mark.asyncio
async def test_evaluate_evidence():
    # Empty chunks -> insufficient
    res1 = await evaluate_evidence_node({"retrieved_chunks": []})
    assert res1["evidence_sufficient"] is False

    # Low similarity chunks -> insufficient
    res2 = await evaluate_evidence_node(
        {"retrieved_chunks": [{"similarity": 0.15}, {"similarity": 0.20}]}
    )
    assert res2["evidence_sufficient"] is False

    # Sufficient similarity -> True
    res3 = await evaluate_evidence_node(
        {"retrieved_chunks": [{"similarity": 0.85}]}
    )
    assert res3["evidence_sufficient"] is True


@pytest.mark.asyncio
async def test_validate_citations_filters_hallucinations():
    retrieved = [
        {
            "chunk_id": "11111111-1111-1111-1111-111111111111",
            "document_id": "doc-1",
            "filename": "annual_report.pdf",
            "page_number": 12,
            "section_title": "Financials",
            "similarity": 0.92,
            "content": "Operating margin was 34%.",
        }
    ]

    # Raw answer cites one real chunk and one hallucinated chunk
    raw_answer = (
        "Operating margin was 34% [Chunk: 11111111-1111-1111-1111-111111111111]. "
        "Also fake fact [Chunk: 99999999-9999-9999-9999-999999999999]."
    )

    result = await validate_citations_node(
        {"raw_answer": raw_answer, "retrieved_chunks": retrieved}
    )

    citations = result["citations"]
    assert len(citations) == 1
    assert citations[0]["chunk_id"] == "11111111-1111-1111-1111-111111111111"
    assert citations[0]["filename"] == "annual_report.pdf"
    assert citations[0]["page_number"] == 12

    # Verify hallucinated citation was not included in validated citations
    assert all(c["chunk_id"] != "99999999-9999-9999-9999-999999999999" for c in citations)
