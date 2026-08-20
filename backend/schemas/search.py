from pydantic import BaseModel, Field, UUID4
from typing import List, Optional, Dict, Any

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The query string to search for.")
    limit: int = Field(5, ge=1, le=50, description="Number of results to return.")

class SearchResult(BaseModel):
    chunk_id: UUID4
    document_id: UUID4
    score: float
    page_number: Optional[int]
    chunk_index: Optional[int]
    text: str
    metadata_: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
