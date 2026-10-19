"""Integration tests for Collections API and cross-user isolation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_collections_crud_and_cross_user_isolation(
    client: AsyncClient,
    user_a_token: str,
    user_b_token: str,
):
    headers_a = {"Authorization": f"Bearer {user_a_token}"}
    headers_b = {"Authorization": f"Bearer {user_b_token}"}

    # 1. Unauthenticated request should fail with 401
    unauth_resp = await client.get("/api/v1/collections")
    assert unauth_resp.status_code == 401

    # 2. User A creates a collection
    create_resp = await client.post(
        "/api/v1/collections",
        json={"name": "User A Private Collection", "description": "Confidential research"},
        headers=headers_a,
    )
    assert create_resp.status_code == 201
    col_a = create_resp.json()
    col_a_id = col_a["id"]
    assert col_a["name"] == "User A Private Collection"

    # 3. User A lists collections -> sees col_a
    list_a_resp = await client.get("/api/v1/collections", headers=headers_a)
    assert list_a_resp.status_code == 200
    assert any(c["id"] == col_a_id for c in list_a_resp.json())

    # 4. Cross-User Isolation: User B lists collections -> does NOT see col_a
    list_b_resp = await client.get("/api/v1/collections", headers=headers_b)
    assert list_b_resp.status_code == 200
    assert all(c["id"] != col_a_id for c in list_b_resp.json())

    # 5. Cross-User Isolation: User B attempts to GET col_a -> receives 404 Not Found
    get_b_resp = await client.get(f"/api/v1/collections/{col_a_id}", headers=headers_b)
    assert get_b_resp.status_code == 404

    # 6. Cross-User Isolation: User B attempts to DELETE col_a -> receives 404 Not Found
    del_b_resp = await client.delete(f"/api/v1/collections/{col_a_id}", headers=headers_b)
    assert del_b_resp.status_code == 404

    # 7. User A updates col_a
    patch_resp = await client.patch(
        f"/api/v1/collections/{col_a_id}",
        json={"name": "User A Updated Collection"},
        headers=headers_a,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "User A Updated Collection"

    # 8. User A deletes col_a -> 204 No Content
    del_a_resp = await client.delete(f"/api/v1/collections/{col_a_id}", headers=headers_a)
    assert del_a_resp.status_code == 204

    # Verify deleted
    get_del_resp = await client.get(f"/api/v1/collections/{col_a_id}", headers=headers_a)
    assert get_del_resp.status_code == 404
