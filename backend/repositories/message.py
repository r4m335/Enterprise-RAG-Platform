import uuid
from typing import List, Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.message import Message

class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user_message(self, conversation_id: str | uuid.UUID, content: str) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role="user",
            content=content
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def create_assistant_message(
        self,
        conversation_id: str | uuid.UUID,
        content: str,
        model: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        citations: Optional[List[Any]] = None
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            citations=citations
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_recent_for_conversation(self, conversation_id: str | uuid.UUID, limit: int = 5) -> List[Message]:
        stmt = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        
        # Return in ascending chronological order
        return list(reversed(messages))
