import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { ChatMessage } from "../../src/components/chat/ChatMessage";
import { Message } from "../../src/types";

describe("ChatMessage", () => {
  const assistantMessage: Message = {
    id: "msg-1",
    conversation_id: "conv-1",
    role: "assistant",
    content: "The system features 256 logical qubits.",
    citations: [
      {
        chunk_id: "c1",
        document_id: "d1",
        filename: "quantum_computing.md",
        page_number: 1,
        similarity_score: 0.95,
        excerpt: "256 logical qubits with error threshold of 99.98%.",
      },
    ],
    created_at: new Date().toISOString(),
  };

  it("renders assistant message content and verified sources badge", () => {
    const handleSelect = vi.fn();
    render(
      <ChatMessage
        message={assistantMessage}
        onSelectCitation={handleSelect}
      />
    );

    expect(screen.getByText(/The system features 256 logical qubits/i)).toBeInTheDocument();
    expect(screen.getByText(/Verified Sources \(1\)/i)).toBeInTheDocument();
    expect(screen.getByText(/quantum_computing.md/i)).toBeInTheDocument();
  });

  it("renders user message without citations", () => {
    const userMsg: Message = {
      id: "msg-2",
      conversation_id: "conv-1",
      role: "user",
      content: "How many qubits?",
      citations: [],
      created_at: new Date().toISOString(),
    };

    render(
      <ChatMessage
        message={userMsg}
        onSelectCitation={vi.fn()}
      />
    );

    expect(screen.getByText("How many qubits?")).toBeInTheDocument();
    expect(screen.queryByText(/Verified Sources/i)).not.toBeInTheDocument();
  });
});
