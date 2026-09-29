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
    document_name: Optional[str] = None
    page_number: Optional[int] = None
    score: float
    text: str

class RetrievalService:
    def __init__(self, qdrant: QdrantService, chunk_repo: ChunkRepository):
        self.qdrant = qdrant
        self.chunk_repo = chunk_repo
        self.embedding_provider = get_embedding_provider()
        
    async def retrieve(self, query: str, user_id: str | uuid.UUID, limit: int = 5) -> List[RetrievedChunk]:
        logger.info(f"Retrieving chunks for query: '{query}', user: {user_id}")
        
        # 1. Embed query
        query_vector = await self.embedding_provider.embed_query(query)
        logger.info("Query embedded successfully, searching Qdrant...")
        
        # 2. Search Qdrant (enforces tenant isolation)
        search_results = await self.qdrant.search(
            query_vector=query_vector, 
            user_id=user_id, 
            limit=limit
        )
        logger.info(f"Qdrant returned {len(search_results)} points")
        
        if not search_results:
            return []
            
        # 3. Hydrate with postgres texts & document names
        chunk_ids = [uuid.UUID(res["chunk_id"]) for res in search_results]
        db_chunks = await self.chunk_repo.get_chunks_by_ids(chunk_ids)
        
        # Hydrate document filenames
        doc_ids = list({c.document_id for c in db_chunks if c.document_id})
        doc_name_map = {}
        if doc_ids:
            try:
                from models.document import Document
                from sqlalchemy import select
                doc_stmt = select(Document.id, Document.original_filename, Document.filename).where(Document.id.in_(doc_ids))
                doc_res = await self.chunk_repo.db.execute(doc_stmt)
                for d in doc_res.all():
                    doc_name_map[str(d[0])] = d[1] or d[2]
            except Exception as e:
                logger.warning(f"Failed to fetch document names in retrieval: {e}")
                
        chunk_map = {
            str(c.id): (c, doc_name_map.get(str(c.document_id), f"Doc {str(c.document_id)[:8]}"))
            for c in db_chunks
        }
        
        retrieved_chunks = []
        for res in search_results:
            c_id = res["chunk_id"]
            if c_id in chunk_map:
                c_model, doc_name = chunk_map[c_id]
                retrieved_chunks.append(
                    RetrievedChunk(
                        chunk_id=c_id,
                        document_id=res["payload"].get("document_id", str(c_model.document_id)),
                        document_name=doc_name,
                        page_number=res["payload"].get("page_number"),
                        score=res["score"],
                        text=c_model.text
                    )
                )
                
        return retrieved_chunks
