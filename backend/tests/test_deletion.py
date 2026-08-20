import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.document import Document, DocumentStatus
from models.chunk import Chunk
from models.user import User
from core.security import get_password_hash, create_access_token

@pytest.fixture
async def token_factory():
    def _create_token(user_id: str):
        return create_access_token(subject=str(user_id))
    return _create_token

@pytest.fixture
async def setup_user(db_session: AsyncSession):
    import uuid
    user = User(
        email=f"test-{uuid.uuid4()}@example.com",
        password_hash=get_password_hash("testpass")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
def mock_celery_task(monkeypatch):
    class MockAsyncResult:
        def __init__(self, task_id):
            self.id = task_id
    
    def mock_delay(*args, **kwargs):
        return MockAsyncResult("fake-task-id")
        
    import workers.tasks.document_processing
    monkeypatch.setattr(workers.tasks.document_processing.process_document_task, "delay", mock_delay)
    return mock_delay

@pytest.fixture
def mock_session_maker(monkeypatch):
    # Tests don't actually process celery, so this is just to mock it if it ever gets called directly.
    pass

@pytest.mark.asyncio
async def test_document_soft_delete_and_qdrant_sync(
    async_client: AsyncClient, 
    db_session: AsyncSession, 
    mock_celery_task, 
    mock_session_maker, 
    token_factory,
    setup_user
):
    user_id = setup_user.id
    token = token_factory(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Upload document
    test_md_content = b"# To be deleted\n\nThis will be deleted."
    response = await async_client.post(
        "/api/v1/documents/",
        headers=headers,
        files={"file": ("test_delete.md", test_md_content, "text/markdown")}
    )
    assert response.status_code == 202
    doc_id = response.json()["document_id"]
    
    # Simulate processing completion so it gets into Qdrant (mocking Qdrant insertion directly)
    # Actually, we can just insert a point into Qdrant directly and verify it's deleted.
    from services.vector_service import QdrantService
    qdrant = QdrantService()
    # ensure collection exists
    await qdrant.initialize_collection(384)
    
    # Upsert a fake chunk
    import uuid
    chunk_id = uuid.uuid4()
    # Fake vector
    vec = [0.1] * 384
    from qdrant_client.http.models import PointStruct
    await qdrant.client.upsert(
        collection_name=qdrant.collection_name,
        points=[
            PointStruct(
                id=str(chunk_id),
                vector=vec,
                payload={
                    "chunk_id": str(chunk_id),
                    "document_id": str(doc_id),
                    "user_id": str(user_id),
                    "text": "test delete text"
                }
            )
        ]
    )
    
    # Verify it exists in Qdrant
    res = await qdrant.search(vec, user_id, limit=1)
    assert len(res) == 1
    assert res[0]["payload"]["document_id"] == str(doc_id)
    
    # 2. Delete document via API
    delete_resp = await async_client.delete(
        f"/api/v1/documents/{doc_id}",
        headers=headers
    )
    assert delete_resp.status_code == 204
    
    # 3. Verify it's soft deleted in DB
    stmt = select(Document).where(Document.id == uuid.UUID(doc_id))
    result = await db_session.execute(stmt)
    doc = result.scalars().first()
    assert doc is not None
    assert doc.deleted_at is not None
    assert doc.processing_status == DocumentStatus.DELETED
    
    # 4. Verify it doesn't appear in GET /api/v1/documents/
    list_resp = await async_client.get("/api/v1/documents/", headers=headers)
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert not any(d["id"] == doc_id for d in docs)
    
    # 5. Verify Qdrant points are deleted
    res_after = await qdrant.search(vec, user_id, limit=1)
    # Could be empty, or not contain our doc_id
    if res_after:
        assert res_after[0]["payload"]["document_id"] != str(doc_id)
    else:
        assert len(res_after) == 0
