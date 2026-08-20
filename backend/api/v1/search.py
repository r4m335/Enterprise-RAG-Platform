import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.deps import get_current_user, get_db
from models.user import User
from schemas.search import SearchRequest, SearchResponse, SearchResult
from rag.embeddings.base import get_embedding_provider
from services.vector_service import QdrantService
from repositories.chunk import ChunkRepository

router = APIRouter()

@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not request.query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty")
        
    provider = get_embedding_provider()
    query_vector = await provider.embed_query(request.query)
    
    qdrant = QdrantService()
    # Security: filter strictly by current_user.id
    qdrant_results = await qdrant.search(
        query_vector=query_vector, 
        user_id=current_user.id, 
        limit=request.limit
    )
    
    if not qdrant_results:
        return SearchResponse(results=[])
        
    # Extract chunk IDs
    chunk_ids = [uuid.UUID(res["chunk_id"]) for res in qdrant_results]
    
    # Fetch from Postgres
    chunk_repo = ChunkRepository(db)
    chunks = await chunk_repo.get_chunks_by_ids(chunk_ids)
    chunk_map = {str(c.id): c for c in chunks}
    
    # Construct ordered response
    results = []
    for res in qdrant_results:
        chunk_id_str = res["chunk_id"]
        db_chunk = chunk_map.get(chunk_id_str)
        if not db_chunk:
            continue
            
        results.append(
            SearchResult(
                chunk_id=db_chunk.id,
                document_id=db_chunk.document_id,
                score=res["score"],
                page_number=db_chunk.page_number,
                chunk_index=db_chunk.chunk_index,
                text=db_chunk.text,
                metadata_=db_chunk.metadata_
            )
        )
        
    return SearchResponse(results=results)
