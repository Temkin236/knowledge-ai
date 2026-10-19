import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { DocumentTable } from "../../src/components/documents/DocumentTable";
import { Document } from "../../src/types";

describe("DocumentTable", () => {
  const mockDocuments: Document[] = [
    {
      id: "doc-1",
      owner_id: "user-1",
      collection_id: "col-1",
      filename: "financial_report.pdf",
      content_type: "application/pdf",
      file_size: 1048576,
      content_hash: "hash123",
      status: "INDEXED",
      chunk_count: 14,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: "doc-2",
      owner_id: "user-1",
      collection_id: "col-1",
      filename: "failed_document.docx",
      content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      file_size: 20480,
      content_hash: "hash456",
      status: "FAILED",
      chunk_count: 0,
      error_message: "Corrupted document header",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  it("renders documents list with status badges and chunk count", () => {
    render(
      <DocumentTable
        documents={mockDocuments}
        onDelete={vi.fn()}
        onRetry={vi.fn()}
      />
    );

    expect(screen.getByText("financial_report.pdf")).toBeInTheDocument();
    expect(screen.getByText("INDEXED")).toBeInTheDocument();
    expect(screen.getByText("14")).toBeInTheDocument();
    expect(screen.getByText("failed_document.docx")).toBeInTheDocument();
    expect(screen.getByText("FAILED")).toBeInTheDocument();
    expect(screen.getByText("Corrupted document header")).toBeInTheDocument();
  });

  it("triggers retry on failed document", () => {
    const handleRetry = vi.fn();
    render(
      <DocumentTable
        documents={mockDocuments}
        onDelete={vi.fn()}
        onRetry={handleRetry}
      />
    );

    const retryBtn = screen.getByTitle("Retry processing");
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledWith("doc-2");
  });

  it("renders empty state when no documents exist", () => {
    render(
      <DocumentTable
        documents={[]}
        onDelete={vi.fn()}
        onRetry={vi.fn()}
      />
    );

    expect(screen.getByText(/No documents indexed yet/i)).toBeInTheDocument();
  });
});
