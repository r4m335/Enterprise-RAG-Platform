import uuid
from typing import List, Dict, Any
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.chunk import Chunk

class ChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def delete_chunks_by_document_id(self, document_id: str | uuid.UUID) -> None:
        if isinstance(document_id, str):
            document_id = uuid.UUID(document_id)
        stmt = delete(Chunk).where(Chunk.document_id == document_id)
        await self.db.execute(stmt)
        await self.db.commit()

    async def bulk_create_chunks(self, document_id: str | uuid.UUID, chunks_data: List[Dict[str, Any]]) -> List[Chunk]:
        if isinstance(document_id, str):
            document_id = uuid.UUID(document_id)
            
        chunks = []
        for idx, data in enumerate(chunks_data):
            db_chunk = Chunk(
                document_id=document_id,
                chunk_index=idx,
                text=data["text"],
                token_count=data["token_count"],
                page_number=data["page_number"],
                metadata_=data["metadata_"]
            )
            chunks.append(db_chunk)
            self.db.add(db_chunk)
            
        await self.db.commit()
        return chunks

    async def get_chunks_by_ids(self, chunk_ids: List[uuid.UUID]) -> List[Chunk]:
        from sqlalchemy import select
        stmt = select(Chunk).where(Chunk.id.in_(chunk_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
