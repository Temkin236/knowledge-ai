"""Chat and Conversations API endpoints integrating the LangGraph RAG workflow."""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.dependencies import CurrentUser, DBSession
from app.rag.graph import build_rag_workflow
from app.rag.prompts import FALLBACK_INSUFFICIENT_EVIDENCE, build_rag_prompt
from app.rag.state import RAGState
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.collection_repository import CollectionRepository
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.common import (
    ChatRequest,
    ChatResponse,
    Citation,
    ConversationResponse,
    MessageResponse,
    RetrievalMetadata,
)
from app.services.embeddings.provider import embedding_provider
from app.services.generation.provider import generation_provider

router = APIRouter(tags=["Chat & Conversations"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: CurrentUser,
    session: DBSession,
):
    """
    Execute a grounded RAG query against a knowledge collection.
    Runs the full inspectable LangGraph workflow and validates citations.
    """
    col_repo = CollectionRepository(session)
    col = await col_repo.get_by_id(payload.collection_id, current_user.id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

    conv_repo = ConversationRepository(session)
    if payload.conversation_id:
        conv = await conv_repo.get_conversation(payload.conversation_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    else:
        # Generate initial title from query snippet
        clean_title = payload.message.strip().replace("\n", " ")[:40]
        conv = await conv_repo.create_conversation(
            owner_id=current_user.id,
            collection_id=payload.collection_id,
            title=clean_title or "New Conversation",
        )

    # Load recent conversation history
    prior_messages = await conv_repo.get_messages(conv.id, current_user.id)
    history = [{"role": m.role, "content": m.content} for m in prior_messages]

    # Initialize typed RAG state
    initial_state: RAGState = {
        "collection_id": str(payload.collection_id),
        "owner_id": str(current_user.id),
        "conversation_id": str(conv.id),
        "query": payload.message,
        "history": history,
        "retry_count": 0,
        "retrieved_chunks": [],
        "evidence_sufficient": True,
        "raw_answer": "",
        "final_answer": "",
        "citations": [],
        "retrieval_metadata": {},
    }

    workflow = build_rag_workflow(session)
    final_state = await workflow.ainvoke(initial_state)

    citations = [
        Citation(
            chunk_id=c["chunk_id"],
            document_id=c["document_id"],
            filename=c["filename"],
            page_number=c.get("page_number"),
            section_title=c.get("section_title"),
            similarity_score=c.get("similarity_score"),
            excerpt=c["excerpt"],
        )
        for c in final_state.get("citations", [])
    ]

    meta = final_state.get("retrieval_metadata", {})
    retrieval_meta = RetrievalMetadata(
        chunks_retrieved=meta.get("chunks_retrieved", 0),
        evidence_sufficient=meta.get("evidence_sufficient", True),
        retries_performed=meta.get("retries_performed", 0),
        duration_ms=meta.get("duration_ms", 0),
        refined_query=meta.get("refined_query"),
    )

    message_id_str = final_state.get("message_id")
    message_id = uuid.UUID(message_id_str) if message_id_str else uuid.uuid4()

    return ChatResponse(
        conversation_id=conv.id,
        message_id=message_id,
        answer=final_state.get("final_answer", ""),
        citations=citations,
        retrieval_metadata=retrieval_meta,
        created_at=datetime.now(timezone.utc),
    )


@router.post("/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    current_user: CurrentUser,
    session: DBSession,
):
    """
    Streams RAG response tokens via Server-Sent Events (SSE).
    Emits token deltas during generation and validates citations upon completion.
    """
    col_repo = CollectionRepository(session)
    col = await col_repo.get_by_id(payload.collection_id, current_user.id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

    conv_repo = ConversationRepository(session)
    if payload.conversation_id:
        conv = await conv_repo.get_conversation(payload.conversation_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    else:
        clean_title = payload.message.strip().replace("\n", " ")[:40]
        conv = await conv_repo.create_conversation(
            owner_id=current_user.id,
            collection_id=payload.collection_id,
            title=clean_title or "New Conversation",
        )

    prior_messages = await conv_repo.get_messages(conv.id, current_user.id)
    history = [{"role": m.role, "content": m.content} for m in prior_messages]

    start_time = time.time()
    query_vec = await embedding_provider.embed_query(payload.message)
    chunk_repo = ChunkRepository(session)
    retrieved = await chunk_repo.similarity_search(
        query_embedding=query_vec,
        collection_id=payload.collection_id,
        owner_id=current_user.id,
        top_k=settings.RETRIEVAL_TOP_K,
        threshold=settings.RETRIEVAL_SIMILARITY_THRESHOLD,
    )
    chunks_data = [r.to_dict() for r in retrieved]

    async def sse_generator() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'event': 'status', 'stage': 'Searching your documents'})}\n\n"
        if not chunks_data:
            # Yield fallback directly
            yield f"data: {json.dumps({'event': 'delta', 'delta': FALLBACK_INSUFFICIENT_EVIDENCE})}\n\n"
            duration_ms = int((time.time() - start_time) * 1000)
            # Persist fallback
            await conv_repo.add_message(conv.id, current_user.id, "user", payload.message)
            msg = await conv_repo.add_message(
                conv.id,
                current_user.id,
                "assistant",
                FALLBACK_INSUFFICIENT_EVIDENCE,
                citations=[],
                retrieval_metadata={"duration_ms": duration_ms, "evidence_sufficient": False},
            )
            await session.commit()
            yield f"data: {json.dumps({'event': 'done', 'conversation_id': str(conv.id), 'message_id': str(msg.id), 'citations': []})}\n\n"
            return

        yield f"data: {json.dumps({'event': 'status', 'stage': 'Checking source evidence'})}\n\n"
        prompt = build_rag_prompt(payload.message, chunks_data, history)
        yield f"data: {json.dumps({'event': 'status', 'stage': 'Writing grounded answer'})}\n\n"
        accumulated_chunks = []

        async for token in generation_provider.generate_stream(prompt):
            accumulated_chunks.append(token)
            yield f"data: {json.dumps({'event': 'delta', 'delta': token})}\n\n"

        full_raw_answer = "".join(accumulated_chunks)

        # Validate citations against retrieved chunks
        from app.rag.nodes import validate_citations_node

        val_result = await validate_citations_node(
            {"raw_answer": full_raw_answer, "retrieved_chunks": chunks_data}
        )
        final_answer = val_result.get("final_answer", full_raw_answer)
        validated_citations = val_result.get("citations", [])

        duration_ms = int((time.time() - start_time) * 1000)
        await conv_repo.add_message(conv.id, current_user.id, "user", payload.message)
        msg = await conv_repo.add_message(
            conv.id,
            current_user.id,
            "assistant",
            final_answer,
            citations=validated_citations,
            retrieval_metadata={
                "duration_ms": duration_ms,
                "chunks_retrieved": len(chunks_data),
                "evidence_sufficient": True,
            },
        )
        await session.commit()

        yield f"data: {json.dumps({'event': 'done', 'conversation_id': str(conv.id), 'message_id': str(msg.id), 'citations': validated_citations})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: CurrentUser,
    session: DBSession,
):
    """List all conversations for the authenticated user."""
    repo = ConversationRepository(session)
    return await repo.list_by_owner(current_user.id)


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    collection_id: uuid.UUID,
    title: Optional[str] = "New Conversation",
    current_user: CurrentUser = None,
    session: DBSession = None,
):
    """Explicitly create a new conversation."""
    col_repo = CollectionRepository(session)
    col = await col_repo.get_by_id(collection_id, current_user.id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

    repo = ConversationRepository(session)
    return await repo.create_conversation(current_user.id, collection_id, title or "New Conversation")


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    session: DBSession,
):
    """Get conversation summary by ID."""
    repo = ConversationRepository(session)
    conv = await repo.get_conversation(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return conv


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    session: DBSession,
):
    """Get chronological message history for a conversation."""
    repo = ConversationRepository(session)
    conv = await repo.get_conversation(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    messages = await repo.get_messages(conversation_id, current_user.id)
    return [
        MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            citations=m.citations or [],
            retrieval_metadata=m.retrieval_metadata or {},
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    session: DBSession,
):
    """Delete a conversation and all its messages."""
    repo = ConversationRepository(session)
    deleted = await repo.delete_conversation(conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return None
