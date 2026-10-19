"""Background worker abstraction for asynchronous document ingestion."""

import asyncio
import uuid
from typing import Dict

from app.core.logging import logger
from app.db.session import async_session_factory
from app.services.ingestion.pipeline import IngestionPipeline


class BackgroundIngestionWorker:
    """
    Asynchronous document ingestion worker.
    Processes document ingestion jobs without blocking the main ASGI web loop.
    Designed with a clean interface that can be backed by Celery or Redis queue in production.
    """

    def __init__(self):
        self._active_tasks: Dict[uuid.UUID, asyncio.Task] = {}

    def submit_ingestion_job(
        self,
        document_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
    ) -> None:
        """Schedules a document for asynchronous processing in the background."""
        task = asyncio.create_task(
            self._execute_job(document_id, file_bytes, filename),
            name=f"ingest-{document_id}",
        )
        self._active_tasks[document_id] = task
        task.add_done_callback(lambda t: self._active_tasks.pop(document_id, None))

    async def _execute_job(
        self,
        document_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
    ) -> None:
        """Executes the ingestion job within an isolated async database session."""
        logger.info(f"Worker starting background ingestion for document {document_id} ({filename})")
        async with async_session_factory() as session:
            pipeline = IngestionPipeline(session)
            try:
                await pipeline.process_document(
                    document_id=document_id,
                    file_bytes=file_bytes,
                    filename=filename,
                )
                logger.info(f"Worker completed ingestion for document {document_id}")
            except Exception as exc:
                logger.error(f"Worker job failed for document {document_id}: {exc}")


# Global background worker instance
ingestion_worker = BackgroundIngestionWorker()
