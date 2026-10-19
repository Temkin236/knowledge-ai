"""Pydantic schemas for data validation and API request/response models."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# User & Auth Schemas
# -----------------------------------------------------------------------------
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: Optional[str] = None
    display_name: Optional[str] = None


# -----------------------------------------------------------------------------
# Collection Schemas
# -----------------------------------------------------------------------------
class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    description: Optional[str] = Field(None, max_length=1000, description="Collection description")


class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class CollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: Optional[str] = None
    document_count: int = 0
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# Document Schemas
# -----------------------------------------------------------------------------
class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    collection_id: uuid.UUID
    filename: str
    content_type: str
    file_size: int
    content_hash: str
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    updated_at: datetime


# -----------------------------------------------------------------------------
# Citation & Chat Schemas
# -----------------------------------------------------------------------------
class Citation(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    similarity_score: Optional[float] = None
    excerpt: str


class RetrievalMetadata(BaseModel):
    chunks_retrieved: int = 0
    evidence_sufficient: bool = True
    retries_performed: int = 0
    duration_ms: int = 0
    refined_query: Optional[str] = None


class ChatRequest(BaseModel):
    collection_id: uuid.UUID
    message: str = Field(..., min_length=1, max_length=4000, description="User question")
    conversation_id: Optional[uuid.UUID] = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    retrieval_metadata: RetrievalMetadata
    created_at: datetime


# -----------------------------------------------------------------------------
# Conversation Schemas
# -----------------------------------------------------------------------------
class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    citations: List[Citation] = Field(default_factory=list)
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    collection_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    collection_id: uuid.UUID
    title: str
    messages: List[MessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
