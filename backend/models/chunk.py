import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from database.base import Base

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    chunk_index = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    
    token_count = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True) # Avoid shadowing SQLAlchemy MetaData
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
