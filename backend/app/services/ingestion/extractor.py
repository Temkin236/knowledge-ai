"""Document text extraction service supporting PDF, DOCX, TXT, and Markdown."""

import io
import re
from dataclasses import dataclass
from typing import List, Optional

import docx
from pypdf import PdfReader

from app.core.logging import logger


@dataclass
class ExtractedSection:
    """A segment of extracted text with associated page or section metadata."""
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None


def normalize_whitespace(text: str) -> str:
    """Normalizes excessive whitespace while preserving meaningful paragraph breaks."""
    # Replace carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-breaking spaces
    text = text.replace("\u00a0", " ")
    # Replace tabs with 4 spaces
    text = text.replace("\t", "    ")
    # Collapse 3 or more consecutive newlines into 2 (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace
    return text.strip()


class DocumentExtractor:
    """Extracts text and structural metadata from supported file formats."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

    @classmethod
    def extract(cls, file_bytes: bytes, filename: str) -> List[ExtractedSection]:
        """Extracts text sections from raw document bytes based on file extension."""
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        ext = f".{ext}"

        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats: PDF, DOCX, TXT, MD.")

        if not file_bytes or len(file_bytes.strip()) == 0:
            raise ValueError("Uploaded file is empty.")

        if ext == ".pdf":
            sections = cls._extract_pdf(file_bytes)
        elif ext == ".docx":
            sections = cls._extract_docx(file_bytes)
        elif ext in (".txt", ".md"):
            sections = cls._extract_plain_text(file_bytes, ext == ".md")
        else:
            raise ValueError(f"Unhandled file extension: {ext}")

        # Validate extracted content
        total_length = sum(len(s.content) for s in sections)
        if total_length < 10:
            raise ValueError(
                "Document text extraction yielded insufficient or unusable content (less than 10 characters)."
            )

        return sections

    @staticmethod
    def _extract_pdf(file_bytes: bytes) -> List[ExtractedSection]:
        """Extracts text page-by-page from a PDF."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            sections: List[ExtractedSection] = []

            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                cleaned = normalize_whitespace(page_text)
                if cleaned:
                    sections.append(
                        ExtractedSection(
                            content=cleaned,
                            page_number=page_idx + 1,  # 1-based page index
                            section_title=None,
                        )
                    )

            if not sections:
                raise ValueError("PDF contains no extractable text (it may be scanned/image-only).")

            return sections
        except Exception as exc:
            if "insufficient" in str(exc) or "image-only" in str(exc):
                raise
            logger.error(f"Failed to parse PDF: {exc}")
            raise ValueError(f"Failed to parse PDF file: {exc}")

    @staticmethod
    def _extract_docx(file_bytes: bytes) -> List[ExtractedSection]:
        """Extracts text from DOCX paragraphs and tables, preserving headings."""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            sections: List[ExtractedSection] = []
            current_heading: Optional[str] = None
            current_buffer: List[str] = []

            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue

                # Check if paragraph style is a heading
                style_name = p.style.name if p.style else ""
                if "heading" in style_name.lower() or "title" in style_name.lower():
                    if current_buffer:
                        full_content = normalize_whitespace("\n".join(current_buffer))
                        if full_content:
                            sections.append(
                                ExtractedSection(
                                    content=full_content,
                                    section_title=current_heading,
                                )
                            )
                        current_buffer = []
                    current_heading = text
                else:
                    current_buffer.append(text)

            # Also extract tables
            for table in doc.tables:
                table_lines = []
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        table_lines.append(row_text)
                if table_lines:
                    current_buffer.append("\n".join(table_lines))

            if current_buffer:
                full_content = normalize_whitespace("\n".join(current_buffer))
                if full_content:
                    sections.append(
                        ExtractedSection(
                            content=full_content,
                            section_title=current_heading,
                        )
                    )

            return sections
        except Exception as exc:
            logger.error(f"Failed to parse DOCX: {exc}")
            raise ValueError(f"Failed to parse DOCX file: {exc}")

    @staticmethod
    def _extract_plain_text(file_bytes: bytes, is_markdown: bool = False) -> List[ExtractedSection]:
        """Extracts text from TXT or Markdown files."""
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        decoded_text = None

        for enc in encodings:
            try:
                decoded_text = file_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if decoded_text is None:
            raise ValueError("Unable to decode text file. Ensure it is encoded in UTF-8 or standard ASCII.")

        cleaned = normalize_whitespace(decoded_text)
        if not cleaned:
            return []

        if not is_markdown:
            return [ExtractedSection(content=cleaned)]

        # For Markdown, split by top-level headers (# or ##) if present
        sections: List[ExtractedSection] = []
        lines = cleaned.split("\n")
        current_heading: Optional[str] = None
        current_buffer: List[str] = []

        for line in lines:
            header_match = re.match(r"^(#{1,3})\s+(.*)$", line.strip())
            if header_match:
                if current_buffer:
                    buf_text = "\n".join(current_buffer).strip()
                    if buf_text:
                        sections.append(
                            ExtractedSection(
                                content=buf_text,
                                section_title=current_heading,
                            )
                        )
                    current_buffer = []
                current_heading = header_match.group(2).strip()
            else:
                current_buffer.append(line)

        if current_buffer:
            buf_text = "\n".join(current_buffer).strip()
            if buf_text:
                sections.append(
                    ExtractedSection(
                        content=buf_text,
                        section_title=current_heading,
                    )
                )

        return sections if sections else [ExtractedSection(content=cleaned)]
