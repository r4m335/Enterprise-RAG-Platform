import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from database.base import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role = Column(String, nullable=False) # e.g. "user", "assistant", "system"
    content = Column(String, nullable=False)
    
    model = Column(String, nullable=True) # e.g. "gpt-4o", "meta-llama/Llama-3-70b-chat-hf"
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    
    citations = Column(JSONB, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
