import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from models.document import Document, DocumentStatus, EmbeddingStatus
from models.chunk import Chunk

@pytest.fixture
async def token_factory():
    def _create_token(user_id):
        from core.security import create_access_token
        return create_access_token(subject=str(user_id))
    return _create_token

@pytest.fixture
async def setup_two_users(db_session: AsyncSession):
    from models.user import User

    user_a = User(email="usera@example.com", password_hash="dummy_hash")
    user_b = User(email="userb@example.com", password_hash="dummy_hash")

    db_session.add(user_a)
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)
    
    doc_a = Document(
        user_id=user_a.id,
        filename="docA.txt", original_filename="docA.txt", storage_path="/path/a",
        processing_status=DocumentStatus.COMPLETED, embedding_status=EmbeddingStatus.COMPLETED
    )
    doc_b = Document(
        user_id=user_b.id,
        filename="docB.txt", original_filename="docB.txt", storage_path="/path/b",
        processing_status=DocumentStatus.COMPLETED, embedding_status=EmbeddingStatus.COMPLETED
    )
    db_session.add(doc_a)
    db_session.add(doc_b)
    await db_session.commit()
    await db_session.refresh(doc_a)
    await db_session.refresh(doc_b)
    
    chunk_a = Chunk(document_id=doc_a.id, text="The quick brown fox jumps over the lazy dog.", chunk_index=0)
    chunk_b = Chunk(document_id=doc_b.id, text="A completely different secret text that user A should not see.", chunk_index=0)
    db_session.add(chunk_a)
    db_session.add(chunk_b)
    await db_session.commit()
    await db_session.refresh(chunk_a)
    await db_session.refresh(chunk_b)
    
    from services.vector_service import QdrantService
    from rag.embeddings.base import get_embedding_provider
    
    provider = get_embedding_provider()
    qdrant = QdrantService()
    await qdrant.initialize_collection(provider.dimension)
    
    vec_a = await provider.embed_documents([chunk_a.text])
    vec_b = await provider.embed_documents([chunk_b.text])
    
    # Needs Document object attached so upsert_chunks can read doc.user_id
    chunk_a.document = doc_a
    chunk_b.document = doc_b
    
    await qdrant.upsert_chunks([chunk_a], vec_a, user_id=user_a.id)
    await qdrant.upsert_chunks([chunk_b], vec_b, user_id=user_b.id)

    return user_a, user_b

@pytest.mark.asyncio
async def test_search_isolation(async_client: AsyncClient, setup_two_users, token_factory):
    user_a, user_b = setup_two_users
    
    token_a = token_factory(user_a.id)
    response = await async_client.post(
        "/api/v1/search/",
        json={"query": "secret text"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Even though query targets User B's content ("secret text"),
    # User A should get zero results because of user isolation.
    for res in data["results"]:
        assert str(res["document_id"]) != str(user_b.id)
