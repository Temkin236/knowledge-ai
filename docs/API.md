# API Specification — Knowledge AI

All API endpoints are versioned under `/api/v1` except system health endpoints.

## Authentication
Protected routes require an `Authorization: Bearer <token>` header containing a valid Supabase JWT.
In development mode with `DEV_MODE_AUTH=true`, a mock bearer token `Bearer dev-token` or valid dev header is accepted.

---

## 1. System Endpoints

### `GET /health`
Liveness probe.
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-10-18T19:00:00Z"
}
```

### `GET /ready`
Readiness probe checking database connectivity and model configuration.
- **Response**: `200 OK` or `503 Service Unavailable`
```json
{
  "status": "ready",
  "database": "connected",
  "gemini_api": "configured"
}
```

---

## 2. Collections Endpoints

### `POST /api/v1/collections`
Create a new knowledge collection.
- **Request Body**:
```json
{
  "name": "Financial Reports 2025",
  "description": "Quarterly earnings and audits"
}
```
- **Response**: `201 Created`

### `GET /api/v1/collections`
List all collections owned by authenticated user.
- **Response**: `200 OK` array of collections with document counts.

### `GET /api/v1/collections/{collection_id}`
Get collection details by ID.
- **Response**: `200 OK`

### `PATCH /api/v1/collections/{collection_id}`
Update collection name or description.
- **Response**: `200 OK`

### `DELETE /api/v1/collections/{collection_id}`
Delete a collection and all associated documents, chunks, and vector embeddings.
- **Response**: `204 No Content`

---

## 3. Documents Endpoints

### `POST /api/v1/collections/{collection_id}/documents`
Upload and trigger background ingestion for a document (`multipart/form-data`).
- **Form Data**:
  - `file`: binary file (PDF, DOCX, TXT, or MD)
- **Response**: `202 Accepted`
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "collection_id": "...",
  "filename": "annual_report.pdf",
  "content_type": "application/pdf",
  "file_size": 1048576,
  "status": "PENDING",
  "chunk_count": 0,
  "created_at": "..."
}
```

### `GET /api/v1/collections/{collection_id}/documents`
List documents in collection with status and chunk count.
- **Response**: `200 OK`

### `GET /api/v1/documents/{document_id}`
Get document detail by ID.
- **Response**: `200 OK`

### `GET /api/v1/documents/{document_id}/status`
Poll indexing status and error diagnostics.
- **Response**: `200 OK`

### `POST /api/v1/documents/{document_id}/retry`
Retry indexing for a document in `FAILED` status.
- **Response**: `202 Accepted`

### `DELETE /api/v1/documents/{document_id}`
Delete a document and immediately cascade-remove all vector embeddings.
- **Response**: `204 No Content`

---

## 4. Chat & Conversations Endpoints

### `POST /api/v1/chat`
Execute a RAG query against a collection.
- **Request Body**:
```json
{
  "collection_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "conversation_id": "optional-uuid",
  "message": "What were the Q3 operating margins?"
}
```
- **Response**: `200 OK`
```json
{
  "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "message_id": "...",
  "answer": "The Q3 operating margin was 28.4% [source: annual_report.pdf, p. 14].",
  "citations": [
    {
      "chunk_id": "...",
      "document_id": "...",
      "filename": "annual_report.pdf",
      "page_number": 14,
      "section_title": "Financial Highlights",
      "similarity_score": 0.884,
      "excerpt": "Operating margin for the third quarter reached 28.4%..."
    }
  ],
  "retrieval_metadata": {
    "chunks_retrieved": 5,
    "evidence_sufficient": true,
    "retries_performed": 0,
    "duration_ms": 782
  }
}
```

### `POST /api/v1/chat/stream`
Stream answer via Server-Sent Events (SSE).
- Streams tokens with `event: delta`
- Emits final validated citations with `event: done`

### `GET /api/v1/conversations`
List user conversations.

### `GET /api/v1/conversations/{conversation_id}`
Get conversation summary.

### `GET /api/v1/conversations/{conversation_id}/messages`
Get full message history for conversation.

### `DELETE /api/v1/conversations/{conversation_id}`
Delete a conversation and message history.
