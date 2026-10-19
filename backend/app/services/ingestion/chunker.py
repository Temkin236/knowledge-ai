"""Document chunking service that splits extracted text into overlapping chunks."""

import uuid
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.models.chunk import DocumentChunk
from app.services.ingestion.extractor import ExtractedSection


class DocumentChunker:
    """Splits extracted text sections into overlapping chunks preserving source metadata."""

    def __init__(
        self,
        chunk_size_tokens: int = settings.CHUNK_SIZE,
        chunk_overlap_tokens: int = settings.CHUNK_OVERLAP,
    ):
        # Approximate 4 characters per token
        self.chunk_size_chars = chunk_size_tokens * 4
        self.chunk_overlap_chars = chunk_overlap_tokens * 4

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size_chars,
            chunk_overlap=self.chunk_overlap_chars,
            length_function=len,
            separators=["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""],
        )

    def chunk_sections(
        self,
        sections: List[ExtractedSection],
        document_id: uuid.UUID,
        collection_id: uuid.UUID,
        owner_id: uuid.UUID,
        source_filename: str,
        content_hash: str,
    ) -> List[DocumentChunk]:
        """Processes extracted sections into persistent DocumentChunk entities."""
        chunks: List[DocumentChunk] = []
        global_index = 0

        for sec in sections:
            if not sec.content or len(sec.content.strip()) == 0:
                continue

            sub_chunks = self.splitter.split_text(sec.content)
            for sub_text in sub_chunks:
                clean_chunk = sub_text.strip()
                if not clean_chunk:
                    continue

                chunk_obj = DocumentChunk(
                    id=uuid.uuid4(),
                    owner_id=owner_id,
                    collection_id=collection_id,
                    document_id=document_id,
                    chunk_index=global_index,
                    content=clean_chunk,
                    page_number=sec.page_number,
                    section_title=sec.section_title,
                    chunk_metadata={
                        "source_filename": source_filename,
                        "content_hash": content_hash,
                        "char_count": len(clean_chunk),
                        "estimated_tokens": max(1, len(clean_chunk) // 4),
                    },
                )
                chunks.append(chunk_obj)
                global_index += 1

        return chunks
