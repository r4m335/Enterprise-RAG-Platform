import uuid
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from services.vector_service import QdrantService
from repositories.chunk import ChunkRepository
from rag.embeddings.base import get_embedding_provider

class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    page_number: Optional[int] = None
    score: float
    text: str

class RetrievalService:
    def __init__(self, qdrant: QdrantService, chunk_repo: ChunkRepository):
        self.qdrant = qdrant
        self.chunk_repo = chunk_repo
        self.embedding_provider = get_embedding_provider()
        
    async def retrieve(self, query: str, user_id: str | uuid.UUID, limit: int = 5) -> List[RetrievedChunk]:
        logger.debug(f"Retrieving chunks for query: '{query}', user: {user_id}")
        
        # 1. Embed query
        query_vectors = await self.embedding_provider.embed_documents([query])
        query_vector = query_vectors[0]
        
        # 2. Search Qdrant (enforces tenant isolation)
        search_results = await self.qdrant.search(
            query_vector=query_vector, 
            user_id=user_id, 
            limit=limit
        )
        
        if not search_results:
            return []
            
        # 3. Hydrate with postgres texts
        chunk_ids = [uuid.UUID(res["chunk_id"]) for res in search_results]
        db_chunks = await self.chunk_repo.get_chunks_by_ids(chunk_ids)
        
        # Map UUID string -> db chunk
        chunk_map = {str(c.id): c for c in db_chunks}
        
        retrieved_chunks = []
        for res in search_results:
            c_id = res["chunk_id"]
            if c_id in chunk_map:
                c_model = chunk_map[c_id]
                retrieved_chunks.append(
                    RetrievedChunk(
                        chunk_id=c_id,
                        document_id=res["payload"].get("document_id", str(c_model.document_id)),
                        page_number=res["payload"].get("page_number"),
                        score=res["score"],
                        text=c_model.text
                    )
                )
                
        return retrieved_chunks
