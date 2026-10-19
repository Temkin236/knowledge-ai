export type DocumentStatus =
  | "PENDING"
  | "EXTRACTING"
  | "CHUNKING"
  | "EMBEDDING"
  | "INDEXED"
  | "FAILED";

export interface User {
  id: string;
  email?: string;
  displayName?: string;
}

export interface Collection {
  id: string;
  owner_id: string;
  name: string;
  description?: string;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  owner_id: string;
  collection_id: string;
  filename: string;
  content_type: string;
  file_size: number;
  content_hash: string;
  status: DocumentStatus;
  chunk_count: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number?: number;
  section_title?: string;
  similarity_score?: number;
  excerpt: string;
}

export interface RetrievalMetadata {
  chunks_retrieved: number;
  evidence_sufficient: boolean;
  retries_performed: number;
  duration_ms: number;
  refined_query?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  retrieval_metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Conversation {
  id: string;
  owner_id: string;
  collection_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}
