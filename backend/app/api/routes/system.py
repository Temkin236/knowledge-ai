"""System health and readiness probes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["System"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Liveness probe returning application state."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(session: AsyncSession = Depends(get_db)):
    """Readiness probe checking database connectivity and provider configuration."""
    checks = {
        "database": "unknown",
        "gemini_api": "configured" if settings.GEMINI_API_KEY else "mock_mode",
    }

    try:
        await session.execute(text("SELECT 1;"))
        checks["database"] = "connected"
    except Exception as exc:
        checks["database"] = f"error: {str(exc)}"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": checks},
        )

    return {"status": "ready", "checks": checks}
