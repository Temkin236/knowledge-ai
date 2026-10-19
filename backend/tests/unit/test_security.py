"""Unit tests for JWT verification and security authentication."""

import uuid
from datetime import timedelta

from app.core.security import create_access_token, verify_supabase_jwt


def test_create_and_verify_valid_token():
    uid = uuid.uuid4()
    token = create_access_token(user_id=uid, email="test@example.com")
    user = verify_supabase_jwt(token)

    assert user is not None
    assert user.id == uid
    assert user.email == "test@example.com"
    assert user.role == "authenticated"


def test_reject_expired_token():
    uid = uuid.uuid4()
    # Expired token in the past
    token = create_access_token(user_id=uid, expires_delta=timedelta(seconds=-10))
    user = verify_supabase_jwt(token)
    assert user is None


def test_reject_invalid_token():
    user = verify_supabase_jwt("not-a-valid-jwt-token")
    assert user is None


def test_dev_mode_token_fallback():
    user = verify_supabase_jwt("dev-token")
    assert user is not None
    assert user.id == uuid.UUID("00000000-0000-0000-0000-000000000001")
