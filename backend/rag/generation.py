import uuid
from typing import List, Tuple, Dict, Any
from loguru import logger

from rag.llm import get_llm_provider
from rag.llm.base import LLMResponse
from rag.retrieval import RetrievalService
from rag.context import ContextBuilder
from models.message import Message

class GenerationService:
    def __init__(self, retrieval_service: RetrievalService):
        self.llm = get_llm_provider()
        self.retrieval = retrieval_service
        
    async def generate_answer(
        self, 
        query: str, 
        history: List[Message], 
        user_id: str | uuid.UUID
    ) -> Tuple[LLMResponse, List[Dict[str, Any]]]:
        """
        Coordinates the RAG process:
        1. Retrieve chunks
        2. Build Context
        3. Call LLM
        4. Return answer and mapped citations
        """
        
        # 1. Retrieval
        retrieved_chunks = await self.retrieval.retrieve(query=query, user_id=user_id, limit=5)
        
        # 2. Context Building
        messages = ContextBuilder.build_messages(
            question=query, 
            history=history, 
            retrieved_chunks=retrieved_chunks
        )
        
        # 3. Generation
        llm_response = await self.llm.generate(messages)
        
        # 4. Map Citations
        citations = []
        for chunk in retrieved_chunks:
            citations.append({
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "page_number": chunk.page_number,
                "score": chunk.score
            })
            
        return llm_response, citations
