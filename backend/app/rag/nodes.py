"""LangGraph nodes implementing each step of the RAG pipeline."""

import re
import time
import uuid
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.rag.prompts import (
    FALLBACK_INSUFFICIENT_EVIDENCE,
    build_query_refinement_prompt,
    build_rag_prompt,
)
from app.rag.state import RAGState
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.conversation_repository import ConversationRepository
from app.services.embeddings.provider import embedding_provider
from app.services.generation.provider import generation_provider


async def validate_and_prepare_query_node(state: RAGState) -> Dict[str, Any]:
    """Validates and normalizes user input query."""
    raw_query = state.get("query", "").strip()
    if not raw_query:
        raise ValueError("Query string cannot be empty.")

    start_time = time.time()
    return {
        "query": raw_query[:4000],
        "retry_count": state.get("retry_count", 0),
        "history": state.get("history", []),
        "retrieval_metadata": {
            "start_time": start_time,
            "retries_performed": 0,
        },
    }


async def retrieve_documents_node(state: RAGState, session: AsyncSession) -> Dict[str, Any]:
    """Generates query embedding and retrieves relevant chunks from pgvector."""
    query_text = state.get("refined_query") or state["query"]
    collection_id = uuid.UUID(str(state["collection_id"]))
    owner_id = uuid.UUID(str(state["owner_id"]))

    logger.info(f"Retrieving chunks for query: '{query_text[:60]}...' in collection {collection_id}")
    query_vec = await embedding_provider.embed_query(query_text)

    chunk_repo = ChunkRepository(session)
    retrieved = await chunk_repo.similarity_search(
        query_embedding=query_vec,
        collection_id=collection_id,
        owner_id=owner_id,
        top_k=settings.RETRIEVAL_TOP_K,
        threshold=settings.RETRIEVAL_SIMILARITY_THRESHOLD,
    )

    chunks_data = [r.to_dict() for r in retrieved]
    logger.info(f"Retrieved {len(chunks_data)} chunks above threshold {settings.RETRIEVAL_SIMILARITY_THRESHOLD}")
    return {"retrieved_chunks": chunks_data}


async def evaluate_evidence_node(state: RAGState) -> Dict[str, Any]:
    """Evaluates whether retrieved evidence is sufficient to ground an answer."""
    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        logger.info("Evidence evaluation: No chunks retrieved.")
        return {"evidence_sufficient": False}

    max_sim = max(c.get("similarity", 0.0) for c in chunks)
    # Require at least one chunk meeting the similarity threshold
    is_sufficient = max_sim >= settings.RETRIEVAL_SIMILARITY_THRESHOLD
    logger.info(f"Evidence evaluation: max_similarity={max_sim:.4f}, sufficient={is_sufficient}")
    return {"evidence_sufficient": is_sufficient}


async def refine_query_node(state: RAGState) -> Dict[str, Any]:
    """Rephrases query for a single targeted retrieval retry."""
    current_retries = state.get("retry_count", 0) + 1
    prompt = build_query_refinement_prompt(state["query"], state.get("history"))
    refined = await generation_provider.generate_answer(
        prompt,
        system_instruction="You are a search query optimizer. Return only the rewritten search query.",
        temperature=0.0,
    )
    clean_refined = refined.strip().strip('"').strip("'")
    logger.info(f"Refined query (retry {current_retries}): '{clean_refined}'")

    meta = state.get("retrieval_metadata", {})
    meta["retries_performed"] = current_retries
    meta["refined_query"] = clean_refined

    return {
        "retry_count": current_retries,
        "refined_query": clean_refined,
        "retrieval_metadata": meta,
    }


async def generate_answer_node(state: RAGState) -> Dict[str, Any]:
    """Generates grounded answer citing source chunk IDs."""
    prompt = build_rag_prompt(
        query=state["query"],
        chunks=state.get("retrieved_chunks", []),
        history=state.get("history", []),
    )
    answer = await generation_provider.generate_answer(prompt)
    return {"raw_answer": answer}


async def generate_fallback_node(state: RAGState) -> Dict[str, Any]:
    """Returns honest abstention message when evidence is insufficient."""
    return {
        "raw_answer": FALLBACK_INSUFFICIENT_EVIDENCE,
        "final_answer": FALLBACK_INSUFFICIENT_EVIDENCE,
        "citations": [],
    }


async def validate_citations_node(state: RAGState) -> Dict[str, Any]:
    """
    Parses citations from raw_answer and validates them against actual retrieved chunks.
    Never permits hallucinated or unretrieved citations.
    """
    raw_answer = state.get("raw_answer", "")
    retrieved_chunks = state.get("retrieved_chunks", [])
    chunk_map = {str(c["chunk_id"]): c for c in retrieved_chunks}

    # Matches [Chunk: <chunk_id>]
    citation_pattern = re.compile(r"\[Chunk:\s*([a-f0-9\-]+)\]", re.IGNORECASE)
    found_matches = citation_pattern.findall(raw_answer)

    validated_citations: List[Dict[str, Any]] = []
    seen_chunk_ids = set()

    for cid in found_matches:
        cid_clean = cid.strip()
        if cid_clean in chunk_map and cid_clean not in seen_chunk_ids:
            seen_chunk_ids.add(cid_clean)
            c_info = chunk_map[cid_clean]
            validated_citations.append(
                {
                    "chunk_id": cid_clean,
                    "document_id": str(c_info.get("document_id")),
                    "filename": c_info.get("filename", "document"),
                    "page_number": c_info.get("page_number"),
                    "section_title": c_info.get("section_title"),
                    "similarity_score": c_info.get("similarity"),
                    "excerpt": c_info.get("content", "")[:300] + "...",
                }
            )

    # Clean the raw answer by replacing [Chunk: <uuid>] with readable badge [Source: filename, p. X]
    def replace_citation(match):
        cid = match.group(1).strip()
        if cid in chunk_map:
            c = chunk_map[cid]
            fn = c.get("filename", "source")
            pn = c.get("page_number")
            return f" [{fn}{f', p. {pn}' if pn else ''}]"
        return ""  # Remove unverified citation

    cleaned_answer = citation_pattern.sub(replace_citation, raw_answer).strip()

    return {
        "final_answer": cleaned_answer or raw_answer,
        "citations": validated_citations,
    }


async def persist_response_node(state: RAGState, session: AsyncSession) -> Dict[str, Any]:
    """Persists conversation messages and citation metadata to the database."""
    conv_id = uuid.UUID(str(state["conversation_id"]))
    owner_id = uuid.UUID(str(state["owner_id"]))

    repo = ConversationRepository(session)

    # Save user message
    await repo.add_message(
        conversation_id=conv_id,
        owner_id=owner_id,
        role="user",
        content=state["query"],
    )

    # Calculate latency
    meta = state.get("retrieval_metadata", {})
    start_time = meta.pop("start_time", None)
    duration_ms = int((time.time() - start_time) * 1000) if start_time else 0
    meta["duration_ms"] = duration_ms
    meta["chunks_retrieved"] = len(state.get("retrieved_chunks", []))
    meta["evidence_sufficient"] = state.get("evidence_sufficient", True)

    # Save assistant message
    msg = await repo.add_message(
        conversation_id=conv_id,
        owner_id=owner_id,
        role="assistant",
        content=state["final_answer"],
        citations=state.get("citations", []),
        retrieval_metadata=meta,
    )

    await session.commit()
    return {
        "message_id": str(msg.id),
        "retrieval_metadata": meta,
    }
