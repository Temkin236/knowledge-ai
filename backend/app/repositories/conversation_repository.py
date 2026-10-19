"""Conversation repository managing chat sessions, messages, and citations."""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message


class ConversationRepository:
    """Handles CRUD queries for Conversations and Messages with strict owner scoping."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_conversation(
        self,
        owner_id: uuid.UUID,
        collection_id: uuid.UUID,
        title: str = "New Conversation",
    ) -> Conversation:
        """Creates a new conversation record."""
        conv = Conversation(
            id=uuid.uuid4(),
            owner_id=owner_id,
            collection_id=collection_id,
            title=title,
        )
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: uuid.UUID,
        load_messages: bool = False,
    ) -> Optional[Conversation]:
        """Retrieves a conversation strictly under owner scope."""
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.owner_id == owner_id,
        )
        if load_messages:
            stmt = stmt.options(selectinload(Conversation.messages))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: uuid.UUID) -> List[Conversation]:
        """Lists all conversations for a user ordered by most recently updated."""
        stmt = (
            select(Conversation)
            .where(Conversation.owner_id == owner_id)
            .order_by(Conversation.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_conversation(self, conversation_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
        """Deletes conversation and cascades to its messages."""
        conv = await self.get_conversation(conversation_id, owner_id)
        if not conv:
            return False

        await self.session.delete(conv)
        await self.session.flush()
        return True

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        owner_id: uuid.UUID,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        retrieval_metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Adds a message to an existing conversation."""
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            owner_id=owner_id,
            role=role,
            content=content,
            citations=citations or [],
            retrieval_metadata=retrieval_metadata or {},
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_messages(self, conversation_id: uuid.UUID, owner_id: uuid.UUID) -> List[Message]:
        """Gets chronological messages for a conversation."""
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.owner_id == owner_id,
            )
            .order_by(Message.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
