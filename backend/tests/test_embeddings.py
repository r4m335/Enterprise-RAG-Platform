import pytest
import uuid
from sqlalchemy import select
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from models.document import Document, DocumentStatus, EmbeddingStatus
from workers.tasks.embedding import _embed_document_async

@pytest.fixture
def mock_session_maker(db_session):
    class MockSessionMaker:
        def __init__(self, session):
            self.session = session
        async def __aenter__(self):
            return self.session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
    with patch("workers.tasks.embedding.AsyncSessionLocal", return_value=MockSessionMaker(db_session)):
        yield

@pytest.mark.asyncio
async def test_empty_document_embedding(db_session: AsyncSession, mock_session_maker):
    from models.user import User
    
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="dummy_hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    doc = Document(
        user_id=user.id,
        filename="empty.txt", original_filename="empty.txt", storage_path="/path",
        processing_status=DocumentStatus.COMPLETED, embedding_status=EmbeddingStatus.PENDING
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    doc_id = str(doc.id)

    # Trigger embedding worker manually
    await _embed_document_async(doc_id)
    
    # Check status
    stmt = select(Document).where(Document.id == uuid.UUID(doc_id))
    result = await db_session.execute(stmt)
    refreshed_doc = result.scalar_one()
    
    assert refreshed_doc.embedding_status == EmbeddingStatus.FAILED
    assert "no chunks available" in refreshed_doc.embedding_error


@pytest.mark.asyncio
async def test_dimension_mismatch():
    from services.vector_service import QdrantService
    
    qdrant = QdrantService()
    
    # If the provider says dimension is 500, but config says 384, it should fail
    with pytest.raises(RuntimeError, match="Dimension mismatch"):
        await qdrant.initialize_collection(provider_dimension=500)
