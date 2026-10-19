"""Typed state schema for the LangGraph RAG workflow."""

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class RAGState(TypedDict, total=False):
    """Execution state passed through each node of the RAG graph."""
    collection_id: str
    owner_id: str
    conversation_id: str
    query: str
    history: List[Dict[str, str]]
    refined_query: Optional[str]
    retry_count: int
    retrieved_chunks: List[Dict[str, Any]]
    evidence_sufficient: bool
    raw_answer: str
    final_answer: str
    citations: List[Dict[str, Any]]
    retrieval_metadata: Dict[str, Any]
    error: Optional[str]
