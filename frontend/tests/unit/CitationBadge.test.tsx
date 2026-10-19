import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { CitationBadge } from "../../src/components/citations/CitationBadge";
import { Citation } from "../../src/types";

describe("CitationBadge", () => {
  const mockCitation: Citation = {
    chunk_id: "chunk-1234",
    document_id: "doc-5678",
    filename: "annual_report.pdf",
    page_number: 14,
    section_title: "Financials",
    similarity_score: 0.88,
    excerpt: "Operating margins reached 34%.",
  };

  it("renders filename, page number, and similarity score", () => {
    const handleClick = vi.fn();
    render(
      <CitationBadge
        citation={mockCitation}
        index={0}
        onClick={handleClick}
      />
    );

    expect(screen.getByText(/annual_report.pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/p. 14/i)).toBeInTheDocument();
    expect(screen.getByText("88%")).toBeInTheDocument();
    expect(screen.getByText("[1]")).toBeInTheDocument();
  });

  it("triggers onClick callback when badge is clicked", () => {
    const handleClick = vi.fn();
    render(
      <CitationBadge
        citation={mockCitation}
        onClick={handleClick}
      />
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
    expect(handleClick).toHaveBeenCalledWith(mockCitation);
  });
});
