import asyncio
from datetime import datetime
from celery import shared_task
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.session import AsyncSessionLocal
from models.document import Document, EmbeddingStatus
from models.chunk import Chunk
from rag.embeddings.base import get_embedding_provider
from services.vector_service import QdrantService
from repositories.document import DocumentRepository

async def _embed_document_async(document_id: str):
    logger.info(f"Starting embedding task for document {document_id}")
    
    async with AsyncSessionLocal() as session:
        doc_repo = DocumentRepository(session)
        doc = await doc_repo.get_document_by_id(document_id)
        
        if not doc:
            logger.error(f"Document {document_id} not found.")
            return

        # Start embedding
        doc.embedding_status = EmbeddingStatus.PROCESSING
        await session.commit()

        try:
            # Load chunks
            stmt = select(Chunk).where(Chunk.document_id == document_id)
            result = await session.execute(stmt)
            chunks = result.scalars().all()

            if not chunks:
                # User specifically requested this to be a terminal validation failure
                doc.embedding_status = EmbeddingStatus.FAILED
                doc.embedding_error = "Empty document: no chunks available for embedding"
                await session.commit()
                logger.warning(f"Document {document_id} has no chunks.")
                return

            provider = get_embedding_provider()
            qdrant_service = QdrantService()
            
            # Ensure collection matches configuration and provider dimension
            await qdrant_service.initialize_collection(provider_dimension=provider.dimension)

            texts = [chunk.text for chunk in chunks]
            
            logger.info(f"Generating embeddings for {len(chunks)} chunks of document {document_id}")
            vectors = await provider.embed_documents(texts)
            
            logger.info(f"Upserting vectors into Qdrant for document {document_id}")
            # Ensure idempotency and user filtering payload
            await qdrant_service.upsert_chunks(chunks, vectors, user_id=doc.user_id)

            # Mark complete
            doc.embedding_status = EmbeddingStatus.COMPLETED
            await session.commit()
            logger.info(f"Successfully embedded document {document_id}")
            
        except Exception as e:
            logger.exception(f"Failed to embed document {document_id}")
            await session.rollback()
            # Fetch again since session might be broken or expired
            doc = await doc_repo.get_document_by_id(document_id)
            if doc:
                doc.embedding_status = EmbeddingStatus.FAILED
                doc.embedding_error = str(e)
                await session.commit()
            raise e


@shared_task(bind=True, max_retries=3)
def embed_document_task(self, document_id: str):
    """
    Celery task to embed a document's chunks and store them in Qdrant.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_embed_document_async(document_id))
        loop.close()
    except Exception as exc:
        logger.error(f"Task failed for document embedding {document_id}. Retrying...")
        self.retry(exc=exc, countdown=60)
