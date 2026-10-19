"""Security, JWT verification, and user authentication module."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger


class AuthenticatedUser(BaseModel):
    """Represents a validated authenticated user session."""
    id: UUID
    email: Optional[str] = None
    role: str = "authenticated"


def create_access_token(
    user_id: UUID,
    email: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed JWT token matching Supabase structure (useful for tests/local dev)."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=24))
    payload = {
        "sub": str(user_id),
        "email": email or "user@example.com",
        "aud": settings.SUPABASE_JWT_AUDIENCE,
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(
        payload,
        settings.SUPABASE_JWT_SECRET,
        algorithm=settings.SUPABASE_JWT_ALGORITHM,
    )


def verify_supabase_jwt(token: str) -> Optional[AuthenticatedUser]:
    """
    Decodes and validates a Supabase JWT token.
    Enforces signature, expiration, and audience checks.
    """
    # Support development/offline mock token if enabled
    if settings.DEV_MODE_AUTH and token in ("dev-token", "test-token", "mock-token"):
        return AuthenticatedUser(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            email="dev@example.com",
            role="authenticated",
        )

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.SUPABASE_JWT_ALGORITHM],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            options={"verify_exp": True, "verify_aud": True},
        )

        user_id_str = payload.get("sub")
        if not user_id_str:
            logger.warning("JWT payload missing 'sub' claim")
            return None

        return AuthenticatedUser(
            id=UUID(user_id_str),
            email=payload.get("email"),
            role=payload.get("role", "authenticated"),
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Provided JWT token has expired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning(f"Invalid JWT token: {exc}")
        return None
    except Exception as exc:
        logger.error(f"Unexpected error validating JWT: {exc}")
        return None
