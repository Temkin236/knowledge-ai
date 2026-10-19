"""Collection repository managing database operations for knowledge collections."""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import Collection
from app.models.document import Document
from app.models.profile import Profile


class CollectionRepository:
    """Handles CRUD queries for Collection entities with strict owner isolation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_profile_exists(self, owner_id: uuid.UUID, display_name: Optional[str] = None) -> Profile:
        """Ensures a profile record exists for the authenticated user."""
        stmt = select(Profile).where(Profile.id == owner_id)
        result = await self.session.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            profile = Profile(id=owner_id, display_name=display_name or "User")
            self.session.add(profile)
            await self.session.flush()
        return profile

    async def create(self, owner_id: uuid.UUID, name: str, description: Optional[str] = None) -> Collection:
        """Creates a collection for the authenticated owner."""
        await self.ensure_profile_exists(owner_id)
        collection = Collection(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name=name,
            description=description,
        )
        self.session.add(collection)
        await self.session.flush()
        return collection

    async def get_by_id(self, collection_id: uuid.UUID, owner_id: uuid.UUID) -> Optional[Collection]:
        """Retrieves collection if and only if owned by the user."""
        stmt = select(Collection).where(
            Collection.id == collection_id,
            Collection.owner_id == owner_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: uuid.UUID) -> List[Tuple[Collection, int]]:
        """Lists all collections for an owner along with their document counts."""
        # Query collections with document count using outer join
        stmt = (
            select(Collection, func.count(Document.id).label("doc_count"))
            .outerjoin(Document, Document.collection_id == Collection.id)
            .where(Collection.owner_id == owner_id)
            .group_by(Collection.id)
            .order_by(Collection.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def update(
        self,
        collection_id: uuid.UUID,
        owner_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Collection]:
        """Updates collection fields strictly under owner scope."""
        collection = await self.get_by_id(collection_id, owner_id)
        if not collection:
            return None

        if name is not None:
            collection.name = name
        if description is not None:
            collection.description = description

        await self.session.flush()
        return collection

    async def delete(self, collection_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
        """Deletes collection and cascades to its documents, chunks, and messages."""
        collection = await self.get_by_id(collection_id, owner_id)
        if not collection:
            return False

        await self.session.delete(collection)
        await self.session.flush()
        return True
