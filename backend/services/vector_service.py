import uuid
from typing import List, Dict, Any
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse

from core.config import settings
from models.chunk import Chunk

class QdrantService:
    def __init__(self):
        url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        
        self.client = AsyncQdrantClient(
            url=url,
            api_key=settings.QDRANT_API_KEY
        )
        self.collection_name = settings.QDRANT_COLLECTION

    async def initialize_collection(self, provider_dimension: int):
        """
        Ensures the collection exists and its dimension matches both the provider and the configuration.
        """
        configured_dimension = settings.EMBEDDING_DIMENSION
        
        if provider_dimension != configured_dimension:
            raise RuntimeError(
                f"Dimension mismatch: Provider dimension ({provider_dimension}) "
                f"does not match configured dimension ({configured_dimension})."
            )

        try:
            # Check if reachable
            collection_info = await self.client.get_collection(self.collection_name)
            
            # Collection exists, check dimension
            existing_dim = collection_info.config.params.vectors.size
            if existing_dim != configured_dimension:
                raise RuntimeError(
                    f"Dimension mismatch: Existing Qdrant collection has dimension {existing_dim}, "
                    f"but system is configured for {configured_dimension}."
                )
            logger.info(f"Qdrant collection '{self.collection_name}' already exists with correct dimension ({existing_dim}).")
            
        except UnexpectedResponse as e:
            if e.status_code == 404:
                # Collection does not exist, create it
                logger.info(f"Creating Qdrant collection '{self.collection_name}' with dimension {configured_dimension}.")
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=configured_dimension, distance=Distance.COSINE)
                )
            else:
                logger.error(f"Failed to connect to Qdrant: {str(e)}")
                raise e
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise e

    async def upsert_chunks(self, chunks: List[Chunk], vectors: List[List[float]], user_id: str | uuid.UUID):
        if len(chunks) != len(vectors):
            raise ValueError("Number of chunks must match number of vectors.")
            
        points = []
        for chunk, vector in zip(chunks, vectors):
            payload = {
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "user_id": str(user_id),
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index
            }

            points.append(PointStruct(
                id=str(chunk.id),
                vector=vector,
                payload=payload
            ))
            
        await self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} points into Qdrant collection '{self.collection_name}'.")

    async def search(self, query_vector: List[float], user_id: str | uuid.UUID, limit: int = 5) -> List[Dict[str, Any]]:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=str(user_id))
                )
            ]
        )
        
        response = await self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True
        )
        
        results = response.points
        if not results:
            return []
            
        return [
            {
                "chunk_id": p.payload.get("chunk_id"),
                "score": p.score,
                "payload": p.payload
            }
            for p in results
        ]

    async def delete_points_for_document(self, document_id: str | uuid.UUID, user_id: str | uuid.UUID):
        """
        Delete all points associated with a document_id and user_id.
        """
        logger.info(f"Deleting points for document '{document_id}', user: '{user_id}'")
        
        doc_filter = Filter(
            must=[
                FieldCondition(key="document_id", match=MatchValue(value=str(document_id))),
                FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))
            ]
        )
        
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=doc_filter
        )
        logger.info(f"Points deleted for document '{document_id}'")
