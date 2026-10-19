import {
  Citation,
  Collection,
  Conversation,
  Document,
  DocumentStatus,
  Message,
  RetrievalMetadata,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

let tokenGetter: () => string | null = () => localStorage.getItem("knowledge_ai_token");

export function setTokenGetter(getter: () => string | null) {
  tokenGetter = getter;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = tokenGetter();
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", "Bearer " + token);
  }

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  // System
  getHealth: () => request<{ status: string; app: string }>("/health"),
  getReady: () => request<{ status: string; checks: Record<string, string> }>("/ready"),

  // Collections
  getCollections: () => request<Collection[]>("/api/v1/collections"),
  getCollection: (id: string) => request<Collection>(`/api/v1/collections/${id}`),
  createCollection: (data: { name: string; description?: string }) =>
    request<Collection>("/api/v1/collections", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateCollection: (id: string, data: { name?: string; description?: string }) =>
    request<Collection>(`/api/v1/collections/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteCollection: (id: string) =>
    request<void>(`/api/v1/collections/${id}`, { method: "DELETE" }),

  // Documents
  getDocuments: (collectionId: string) =>
    request<Document[]>(`/api/v1/collections/${collectionId}/documents`),
  uploadDocument: (collectionId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<Document>(`/api/v1/collections/${collectionId}/documents`, {
      method: "POST",
      body: formData,
    });
  },
  getDocument: (id: string) => request<Document>(`/api/v1/documents/${id}`),
  getDocumentStatus: (id: string) =>
    request<{
      id: string;
      status: DocumentStatus;
      chunk_count: number;
      error_message?: string;
      updated_at: string;
    }>(`/api/v1/documents/${id}/status`),
  retryDocument: (id: string) =>
    request<Document>(`/api/v1/documents/${id}/retry`, { method: "POST" }),
  deleteDocument: (id: string) =>
    request<void>(`/api/v1/documents/${id}`, { method: "DELETE" }),

  // Chat
  sendChatMessage: (data: {
    collection_id: string;
    message: string;
    conversation_id?: string;
  }) =>
    request<{
      conversation_id: string;
      message_id: string;
      answer: string;
      citations: Citation[];
      retrieval_metadata: RetrievalMetadata;
      created_at: string;
    }>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  sendChatMessageStream: async (
    data: {
      collection_id: string;
      message: string;
      conversation_id?: string;
    },
    onEvent: (event: {
      event: "status" | "delta" | "done" | "error";
      stage?: string;
      delta?: string;
      conversation_id?: string;
      message_id?: string;
      citations?: Citation[];
      message?: string;
    }) => void,
  ) => {
    const token = tokenGetter();
    const headers = new Headers({ "Content-Type": "application/json" });
    if (token) {
      headers.set("Authorization", "Bearer " + token);
    }

    const response = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok || !response.body) {
      let errorDetail = "Unable to start the streamed response.";
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || JSON.stringify(errJson);
      } catch {
        errorDetail = response.statusText || errorDetail;
      }
      throw new Error(errorDetail);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    const consumeEvent = (rawEvent: string) => {
      const dataLine = rawEvent
        .split("\n")
        .find((line) => line.startsWith("data:"));
      if (!dataLine) return;

      let event: Parameters<typeof onEvent>[0];
      try {
        event = JSON.parse(dataLine.slice(5).trim());
      } catch {
        throw new Error("Received an invalid streaming response from the server.");
      }
      onEvent(event);
    };

    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";
      events.forEach(consumeEvent);
      if (done) break;
    }

    if (buffer.trim()) consumeEvent(buffer);
  },

  // Conversations
  getConversations: () => request<Conversation[]>("/api/v1/conversations"),
  createConversation: (collectionId: string, title?: string) =>
    request<Conversation>("/api/v1/conversations", {
      method: "POST",
      body: JSON.stringify({ collection_id: collectionId, title }),
    }),
  getConversation: (id: string) => request<Conversation>(`/api/v1/conversations/${id}`),
  getConversationMessages: (id: string) =>
    request<Message[]>(`/api/v1/conversations/${id}/messages`),
  deleteConversation: (id: string) =>
    request<void>(`/api/v1/conversations/${id}`, { method: "DELETE" }),
};
