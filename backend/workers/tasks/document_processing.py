import asyncio
from datetime import datetime
from celery import shared_task
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database.session import AsyncSessionLocal
from models.document import DocumentStatus
from rag.parser import parse_document
from rag.chunking import chunk_document
from services.storage import get_storage_provider
from repositories.document import DocumentRepository
from repositories.chunk import ChunkRepository

async def _process_document_async(document_id: str):
    logger.info(f"Starting processing for document {document_id}")
    
    async with AsyncSessionLocal() as session:
        doc_repo = DocumentRepository(session)
        chunk_repo = ChunkRepository(session)
        
        # Load Document
        doc = await doc_repo.get_document_by_id(document_id)
        
        if not doc:
            logger.error(f"Document {document_id} not found.")
            return
            
        if doc.status == DocumentStatus.COMPLETED:
            logger.info(f"Document {document_id} is already COMPLETED. Skipping.")
            return
            
        try:
            # Mark as processing
            doc = await doc_repo.update_document_status(document_id, DocumentStatus.PROCESSING)
            
            # Fetch file
            storage = get_storage_provider(doc.storage_provider)
            file_stream = await storage.get(doc.storage_path)
            file_bytes = file_stream.read()
            file_stream.close()
            
            # Delete existing chunks if retrying
            await chunk_repo.delete_chunks_by_document_id(document_id)
            
            # Parse Document
            parsed_doc = parse_document(file_bytes, doc.mime_type)
            
            # Chunk Document
            chunks = chunk_document(parsed_doc)
            
            # Persist Chunks
            chunks_data = [
                {
                    "text": c.text,
                    "token_count": c.token_count,
                    "page_number": c.page_number,
                    "metadata_": c.metadata
                }
                for c in chunks
            ]
            await chunk_repo.bulk_create_chunks(document_id, chunks_data)
                
            # Update Document status
            await doc_repo.update_document_processing_result(
                document_id, 
                status=DocumentStatus.COMPLETED,
                processed_at=datetime.utcnow()
            )
            
            logger.info(f"Successfully processed document {document_id}")
            
        except Exception as e:
            logger.exception(f"Failed to process document {document_id}")
            await session.rollback()
            await doc_repo.update_document_processing_result(
                document_id, 
                status=DocumentStatus.FAILED,
                error_msg=str(e),
                processed_at=datetime.utcnow()
            )
            raise e

@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """
    Celery task that acts as a synchronous wrapper around the async document processing logic.
    """
    try:
        # Run async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_process_document_async(document_id))
        loop.close()
    except Exception as exc:
        logger.error(f"Task failed for document {document_id}. Retrying...")
        self.retry(exc=exc, countdown=60) # Retry after 1 minute
