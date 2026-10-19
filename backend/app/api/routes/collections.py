"""Collections API endpoints."""

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DBSession
from app.repositories.collection_repository import CollectionRepository
from app.schemas.common import CollectionCreate, CollectionResponse, CollectionUpdate

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    payload: CollectionCreate,
    current_user: CurrentUser,
    session: DBSession,
):
    """Create a new knowledge collection."""
    repo = CollectionRepository(session)
    col = await repo.create(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    return CollectionResponse(
        id=col.id,
        owner_id=col.owner_id,
        name=col.name,
        description=col.description,
        document_count=0,
        created_at=col.created_at,
        updated_at=col.updated_at,
    )


@router.get("", response_model=List[CollectionResponse])
async def list_collections(
    current_user: CurrentUser,
    session: DBSession,
):
    """List all collections owned by current user."""
    repo = CollectionRepository(session)
    rows = await repo.list_by_owner(current_user.id)
    return [
        CollectionResponse(
            id=col.id,
            owner_id=col.owner_id,
            name=col.name,
            description=col.description,
            document_count=count,
            created_at=col.created_at,
            updated_at=col.updated_at,
        )
        for col, count in rows
    ]


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: uuid.UUID,
    current_user: CurrentUser,
    session: DBSession,
):
    """Get collection details by ID."""
    repo = CollectionRepository(session)
    col = await repo.get_by_id(collection_id, current_user.id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

    rows = await repo.list_by_owner(current_user.id)
    count = next((c for c_obj, c in rows if c_obj.id == collection_id), 0)

    return CollectionResponse(
        id=col.id,
        owner_id=col.owner_id,
        name=col.name,
        description=col.description,
        document_count=count,
        created_at=col.created_at,
        updated_at=col.updated_at,
    )


@router.patch("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: uuid.UUID,
    payload: CollectionUpdate,
    current_user: CurrentUser,
    session: DBSession,
):
    """Update a collection name or description."""
    repo = CollectionRepository(session)
    col = await repo.update(
        collection_id=collection_id,
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

    return CollectionResponse(
        id=col.id,
        owner_id=col.owner_id,
        name=col.name,
        description=col.description,
        document_count=0,
        created_at=col.created_at,
        updated_at=col.updated_at,
    )


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: uuid.UUID,
    current_user: CurrentUser,
    session: DBSession,
):
    """Delete a collection and all associated documents, chunks, and messages."""
    repo = CollectionRepository(session)
    deleted = await repo.delete(collection_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
    return None
