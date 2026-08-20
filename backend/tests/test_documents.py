import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch
import os

from main import app
from models.user import User
from models.document import Document, DocumentStatus
from models.chunk import Chunk
from api.deps import get_current_user
from workers.tasks.document_processing import _process_document_async

# Create a dummy user
dummy_user_id = uuid.uuid4()
dummy_user = User(id=dummy_user_id, email="test_e2e@example.com")

async def override_get_current_user():
    return dummy_user

app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture(autouse=True)
async def setup_user(db_session: AsyncSession):
    user = await db_session.get(User, dummy_user_id)
    if not user:
        new_user = User(id=dummy_user_id, email="test_e2e@example.com", password_hash="dummy")
        db_session.add(new_user)
        await db_session.commit()


@pytest.fixture
def mock_celery_task():
    with patch("workers.tasks.document_processing.process_document_task.delay") as mock_process:
        with patch("workers.tasks.document_processing.embed_document_task.delay") as mock_embed:
            yield mock_process

@pytest.fixture
def mock_session_maker(db_session):
    # We mock the session maker so the background task uses our test DB session
    class MockSessionMaker:
        def __init__(self, session):
            self.session = session
        async def __aenter__(self):
            return self.session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
    with patch("workers.tasks.document_processing.AsyncSessionLocal", return_value=MockSessionMaker(db_session)):
        yield

@pytest.mark.asyncio
async def test_end_to_end_document_ingestion(async_client: AsyncClient, db_session: AsyncSession, mock_celery_task, mock_session_maker, tmp_path):
    # 1. Prepare a dummy PDF file
    file_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n" # Very basic dummy PDF structure. But we might need a real-ish one.
    # Actually, PyMuPDF might crash on a fake PDF. Let's create a valid minimal markdown file instead since we support multiple types.
    test_md_content = b"# Test Document\n\nThis is a test paragraph that should be chunked properly. Page one."
    
    # 2. Upload the document via API
    response = await async_client.post(
        "/api/v1/documents/",
        files={"file": ("test_doc.md", test_md_content, "text/markdown")}
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "document_id" in data
    document_id = data["document_id"]
    
    # Verify the Celery task was enqueued
    mock_celery_task.assert_called_once_with(document_id)
    
    # 3. Verify Database state = UPLOADED
    stmt = select(Document).where(Document.id == uuid.UUID(document_id))
    result = await db_session.execute(stmt)
    doc = result.scalar_one_or_none()
    assert doc is not None
    assert doc.processing_status == DocumentStatus.UPLOADED
    assert doc.user_id == dummy_user_id
    
    # 4. Trigger the processing synchronously (mocking Celery worker)
    # The _process_document_async uses our mock_session_maker so it connects to test DB.
    await _process_document_async(document_id)
    
    # 5. Verify Database state = COMPLETED
    await db_session.refresh(doc)
    assert doc.processing_status == DocumentStatus.COMPLETED
    
    # 6. Verify Chunks exist and validate metadata/pagination
    stmt_chunks = select(Chunk).where(Chunk.document_id == uuid.UUID(document_id)).order_by(Chunk.page_number)
    result_chunks = await db_session.execute(stmt_chunks)
    chunks = result_chunks.scalars().all()
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.document_id == uuid.UUID(document_id)
        assert chunk.page_number is not None
        assert chunk.text != ""
        assert "mime_type" in chunk.metadata_
    
    # 7. Test Idempotency: Process again!
    await _process_document_async(document_id)
    
    # Verify we didn't duplicate chunks
    result_chunks_2 = await db_session.execute(stmt_chunks)
    chunks_2 = result_chunks_2.scalars().all()
    assert len(chunks) == len(chunks_2)
    
@pytest.mark.asyncio
async def test_document_ingestion_failure(async_client: AsyncClient, db_session: AsyncSession, mock_celery_task, mock_session_maker):
    # Upload an invalid file pretending to be text
    response = await async_client.post(
        "/api/v1/documents/",
        files={"file": ("test_bad.md", b"BAD_BYTES_THAT_WILL_FAIL_PARSER", "text/markdown")}
    )
    
    assert response.status_code == 202
    document_id = response.json()["document_id"]
    
    # Force a failure in the parser by patching parse_document
    with patch("workers.tasks.document_processing.parse_document", side_effect=ValueError("Parsing failed!")):
        with pytest.raises(ValueError):
            await _process_document_async(document_id)
            
    # Verify FAILED status
    stmt = select(Document).where(Document.id == uuid.UUID(document_id))
    result = await db_session.execute(stmt)
    doc = result.scalar_one_or_none()
    assert doc.processing_status == DocumentStatus.FAILED
    assert doc.processing_error == "Parsing failed!"
