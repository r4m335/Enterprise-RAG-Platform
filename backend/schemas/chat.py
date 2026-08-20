import uuid
from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[uuid.UUID] = None

class Citation(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    page_number: Optional[int] = None
    score: float

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    answer: str
    citations: List[Citation]
    usage: TokenUsage
