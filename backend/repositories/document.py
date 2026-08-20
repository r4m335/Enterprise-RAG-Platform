from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.document import Document, DocumentStatus

class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(self, user_id: uuid.UUID, document_id: uuid.UUID, filename: str, mime_type: str, file_size: int, storage_path: str, storage_provider: str) -> Document:
        doc = Document(
            id=document_id,
            user_id=user_id,
            filename=filename,
            original_filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            storage_path=storage_path,
            storage_provider=storage_provider,
            processing_status=DocumentStatus.UPLOADED
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def get_document_by_id(self, document_id: str | uuid.UUID) -> Optional[Document]:
        if isinstance(document_id, str):
            document_id = uuid.UUID(document_id)
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_document_processing_status(self, document_id: str | uuid.UUID, status: DocumentStatus) -> Optional[Document]:
        doc = await self.get_document_by_id(document_id)
        if doc:
            doc.processing_status = status
            await self.db.commit()
            await self.db.refresh(doc)
        return doc
        
    async def update_document_processing_result(self, document_id: str | uuid.UUID, status: DocumentStatus, error_msg: Optional[str] = None, processed_at=None) -> Optional[Document]:
        doc = await self.get_document_by_id(document_id)
        if doc:
            doc.processing_status = status
            doc.processing_error = error_msg
            if processed_at:
                doc.processed_at = processed_at
            await self.db.commit()
            await self.db.refresh(doc)
        return doc
