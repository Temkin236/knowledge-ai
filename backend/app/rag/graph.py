"""LangGraph workflow assembly with typed state, conditional routing, and retry bounds."""

from typing import Any, Dict, Literal

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.rag.nodes import (
    evaluate_evidence_node,
    generate_answer_node,
    generate_fallback_node,
    persist_response_node,
    refine_query_node,
    retrieve_documents_node,
    validate_and_prepare_query_node,
    validate_citations_node,
)
from app.rag.state import RAGState


def build_rag_workflow(session: AsyncSession):
    """
    Constructs and compiles the explicit LangGraph RAG workflow.
    Binds the active database session to repository-accessing nodes.
    """
    workflow = StateGraph(RAGState)

    # 1. Add Nodes
    workflow.add_node("validate_and_prepare_query", validate_and_prepare_query_node)

    async def retrieve_docs_wrapper(state: RAGState) -> Dict[str, Any]:
        return await retrieve_documents_node(state, session)

    workflow.add_node("retrieve_documents", retrieve_docs_wrapper)
    workflow.add_node("evaluate_evidence", evaluate_evidence_node)
    workflow.add_node("refine_query", refine_query_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("generate_fallback", generate_fallback_node)
    workflow.add_node("validate_citations", validate_citations_node)

    async def persist_response_wrapper(state: RAGState) -> Dict[str, Any]:
        return await persist_response_node(state, session)

    workflow.add_node("persist_response", persist_response_wrapper)

    # 2. Add Edges & Conditional Routing
    workflow.set_entry_point("validate_and_prepare_query")
    workflow.add_edge("validate_and_prepare_query", "retrieve_documents")
    workflow.add_edge("retrieve_documents", "evaluate_evidence")

    def route_evidence(state: RAGState) -> Literal["generate_answer", "refine_query", "generate_fallback"]:
        if state.get("evidence_sufficient", False):
            return "generate_answer"
        if state.get("retry_count", 0) < settings.MAX_RETRIES and settings.ENABLE_QUERY_REFINEMENT:
            return "refine_query"
        return "generate_fallback"

    workflow.add_conditional_edges(
        "evaluate_evidence",
        route_evidence,
        {
            "generate_answer": "generate_answer",
            "refine_query": "refine_query",
            "generate_fallback": "generate_fallback",
        },
    )

    # Retry loop: refine_query goes back to retrieve_documents
    workflow.add_edge("refine_query", "retrieve_documents")

    # Both generation paths converge to citation validation
    workflow.add_edge("generate_answer", "validate_citations")
    workflow.add_edge("generate_fallback", "validate_citations")

    # Validation persists to database and terminates
    workflow.add_edge("validate_citations", "persist_response")
    workflow.add_edge("persist_response", END)

    return workflow.compile()
