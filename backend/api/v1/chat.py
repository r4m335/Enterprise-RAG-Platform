import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.deps import get_db, get_current_user
from models.user import User
from schemas.chat import ChatRequest, ChatResponse, Citation, TokenUsage
from repositories.conversation import ConversationRepository
from repositories.message import MessageRepository
from repositories.chunk import ChunkRepository
from services.vector_service import QdrantService
from rag.retrieval import RetrievalService
from rag.generation import GenerationService
from core.config import settings

router = APIRouter()

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    
    # 1. Resolve conversation_id (ownership check)
    if request.conversation_id:
        conversation = await conv_repo.get_for_user(request.conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conversation_id = conversation.id
    else:
        conversation = await conv_repo.create(user_id=current_user.id)
        conversation_id = conversation.id
        
    # 2. Get history (last N individual messages)
    history = await msg_repo.get_recent_for_conversation(
        conversation_id, 
        limit=settings.CHAT_HISTORY_MESSAGES
    )
    
    # 3. Store user message
    user_msg = await msg_repo.create_user_message(
        conversation_id=conversation_id,
        content=request.query
    )
    
    # 4. Generate Answer
    qdrant = QdrantService()
    chunk_repo = ChunkRepository(db)
    retrieval = RetrievalService(qdrant, chunk_repo)
    generation = GenerationService(retrieval)
    
    llm_resp, citations = await generation.generate_answer(
        query=request.query,
        history=history,
        user_id=current_user.id
    )
    
    # 5. Store assistant message
    assistant_msg = await msg_repo.create_assistant_message(
        conversation_id=conversation_id,
        content=llm_resp.content,
        model=llm_resp.model,
        prompt_tokens=llm_resp.prompt_tokens,
        completion_tokens=llm_resp.completion_tokens,
        citations=citations
    )
    
    # 6. Return response
    return ChatResponse(
        conversation_id=conversation_id,
        answer=llm_resp.content,
        citations=[Citation(**c) for c in citations],
        usage=TokenUsage(
            prompt_tokens=llm_resp.prompt_tokens,
            completion_tokens=llm_resp.completion_tokens,
            total_tokens=llm_resp.total_tokens
        )
    )
