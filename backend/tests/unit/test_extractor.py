"""Unit tests for DocumentExtractor and whitespace normalization."""

import pytest

from app.services.ingestion.extractor import DocumentExtractor, normalize_whitespace


def test_normalize_whitespace():
    raw = "Hello   world!\r\n\r\n\r\nThis is\ta   test.\u00a0"
    cleaned = normalize_whitespace(raw)
    assert "Hello   world!" in cleaned
    assert "\r" not in cleaned
    assert "\u00a0" not in cleaned
    # Multiple empty lines should collapse to at most double newlines
    assert "\n\n\n" not in cleaned


def test_extract_plain_text():
    text = "Knowledge AI is an advanced RAG assistant.\nIt grounds answers in source documents."
    sections = DocumentExtractor.extract(text.encode("utf-8"), "test.txt")
    assert len(sections) >= 1
    assert "Knowledge AI" in sections[0].content


def test_extract_markdown_with_headers():
    md = """# Introduction
Knowledge AI provides grounded answers.

## Architecture
It uses FastAPI and LangGraph.
"""
    sections = DocumentExtractor.extract(md.encode("utf-8"), "doc.md")
    assert len(sections) == 2
    assert sections[0].section_title == "Introduction"
    assert "grounded answers" in sections[0].content
    assert sections[1].section_title == "Architecture"
    assert "FastAPI" in sections[1].content


def test_empty_document_rejection():
    with pytest.raises(ValueError, match="empty|insufficient"):
        DocumentExtractor.extract(b"", "empty.txt")

    with pytest.raises(ValueError, match="empty|insufficient"):
        DocumentExtractor.extract(b"  \n  ", "spaces.txt")

    with pytest.raises(ValueError, match="insufficient"):
        DocumentExtractor.extract(b"short", "tiny.txt")


def test_unsupported_file_rejection():
    with pytest.raises(ValueError, match="Unsupported file format"):
        DocumentExtractor.extract(b"Some text", "image.png")
