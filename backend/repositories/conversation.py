import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.conversation import Conversation

class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create(self, user_id: str | uuid.UUID) -> Conversation:
        conversation = Conversation(user_id=user_id)
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def get_for_user(self, conversation_id: str | uuid.UUID, user_id: str | uuid.UUID) -> Optional[Conversation]:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
