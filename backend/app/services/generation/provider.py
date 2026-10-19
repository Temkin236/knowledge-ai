"""Generation provider supporting Google Gemini with streaming and test mock fallback."""

import asyncio
from typing import AsyncGenerator, Optional

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging import logger
from app.rag.prompts import FALLBACK_INSUFFICIENT_EVIDENCE, RAG_SYSTEM_PROMPT


class GenerationProvider:
    """Manages answer generation using Google Gemini with fallback for isolated tests."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = settings.GENERATION_MODEL,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    async def generate_answer(
        self,
        prompt: str,
        system_instruction: str = RAG_SYSTEM_PROMPT,
        temperature: float = 0.2,
    ) -> str:
        """Generates an answer using Google Gemini."""
        if not self.client or not self.api_key:
            return self._mock_generate(prompt)

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=1500,
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            return response.text or ""
        except Exception as exc:
            logger.error(f"Gemini generation error: {exc}")
            raise RuntimeError(f"Failed to generate answer from Gemini: {exc}")

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str = RAG_SYSTEM_PROMPT,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        """Streams generated tokens asynchronously."""
        if not self.client or not self.api_key:
            full_text = self._mock_generate(prompt)
            # Yield in word chunks to simulate streaming
            words = full_text.split(" ")
            for w in words:
                yield w + " "
                await asyncio.sleep(0.01)
            return

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=1500,
            )
            response_stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as exc:
            logger.error(f"Gemini streaming error: {exc}")
            raise RuntimeError(f"Streaming generation failed: {exc}")

    def _mock_generate(self, prompt: str) -> str:
        """
        Deterministic mock generator for offline automated tests.
        Inspects evidence blocks in prompt; if evidence is present, extracts key sentences
        and attaches citation badges [Chunk: <chunk_id>].
        """
        import re

        evidence_matches = list(re.finditer(r'<evidence id="([^"]+)"[^>]*>(.*?)</evidence>', prompt, re.DOTALL))
        if not evidence_matches:
            return FALLBACK_INSUFFICIENT_EVIDENCE

        # Extract user query
        query_match = re.search(r"User Question:\s*(.*?)(?:\n\s*Provide|\Z)", prompt, re.DOTALL)
        query = query_match.group(1).strip().lower() if query_match else ""

        # Find evidence that matches query terms
        query_words = set(w for w in re.findall(r"\w+", query) if len(w) > 3)
        entity_stops = {"helios", "labs", "project", "system", "what", "which", "when", "where", "does", "have"}
        predicates = set(w for w in query_words if w not in entity_stops)

        matched_sentences = []
        best_chunk_id = None

        for match in evidence_matches:
            chunk_id = match.group(1)
            content = match.group(2).strip()
            sentences = re.split(r"(?<=[.!?])\s+", content)
            for sentence in sentences:
                sent_words = set(w.lower() for w in re.findall(r"\w+", sentence))
                # Must match predicate keywords if present
                if predicates and not predicates.intersection(sent_words):
                    continue
                overlap = len(query_words.intersection(sent_words))
                if overlap >= 1:
                    matched_sentences.append(sentence.strip())
                    if not best_chunk_id:
                        best_chunk_id = chunk_id

        if matched_sentences and best_chunk_id:
            combined = " ".join(matched_sentences)
            return f"According to the source documents, {combined} [Chunk: {best_chunk_id}]"

        return FALLBACK_INSUFFICIENT_EVIDENCE


# Global generation provider singleton
generation_provider = GenerationProvider()
