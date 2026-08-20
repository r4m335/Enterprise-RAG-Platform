import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from models.document import Document, DocumentStatus, EmbeddingStatus
from models.chunk import Chunk
from models.conversation import Conversation
from models.message import Message
from sqlalchemy import select

@pytest.fixture
async def token_factory():
    def _create_token(user_id):
        from core.security import create_access_token
        return create_access_token(subject=str(user_id))
    return _create_token

@pytest.fixture
async def setup_users_and_chunks(db_session: AsyncSession):
    from models.user import User

    user_a = User(email="user_a_chat@example.com", password_hash="dummy")
    user_b = User(email="user_b_chat@example.com", password_hash="dummy")

    db_session.add(user_a)
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)
    
    doc_a = Document(
        user_id=user_a.id,
        filename="policy.txt", original_filename="policy.txt", storage_path="/path/a",
        processing_status=DocumentStatus.COMPLETED, embedding_status=EmbeddingStatus.COMPLETED
    )
    doc_b = Document(
        user_id=user_b.id,
        filename="secret.txt", original_filename="secret.txt", storage_path="/path/b",
        processing_status=DocumentStatus.COMPLETED, embedding_status=EmbeddingStatus.COMPLETED
    )
    db_session.add(doc_a)
    db_session.add(doc_b)
    await db_session.commit()
    await db_session.refresh(doc_a)
    await db_session.refresh(doc_b)
    
    chunk_a = Chunk(document_id=doc_a.id, text="Employees must rotate passwords every 90 days.", chunk_index=0)
    chunk_b = Chunk(document_id=doc_b.id, text="User B secret password is 123", chunk_index=0)
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
    
    chunk_a.document = doc_a
    chunk_b.document = doc_b
    
    await qdrant.upsert_chunks([chunk_a], vec_a, user_id=user_a.id)
    await qdrant.upsert_chunks([chunk_b], vec_b, user_id=user_b.id)

    return user_a, user_b, chunk_a, chunk_b

@pytest.fixture(autouse=True)
def force_fake_llm(monkeypatch):
    from core.config import settings
    monkeypatch.setattr(settings, "LLM_PROVIDER", "fake")

@pytest.mark.asyncio
async def test_chat_end_to_end_and_isolation(async_client: AsyncClient, setup_users_and_chunks, token_factory, db_session: AsyncSession):
    user_a, user_b, chunk_a, chunk_b = setup_users_and_chunks
    token_a = token_factory(user_a.id)
    
    # 1. Ask a question (Conversation creation + Generation)
    response = await async_client.post(
        "/api/v1/chat/",
        json={"query": "What is the password policy?"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["answer"] == "Employees must rotate passwords every 90 days."
    assert len(data["citations"]) > 0
    
    # Verify isolation (chunk B should never be cited)
    for cite in data["citations"]:
        assert str(cite["chunk_id"]) != str(chunk_b.id)
        assert str(cite["chunk_id"]) == str(chunk_a.id)
        
    conversation_id = data["conversation_id"]
    
    # 2. Check persistence
    stmt = select(Message).where(Message.conversation_id == uuid.UUID(conversation_id)).order_by(Message.timestamp)
    result = await db_session.execute(stmt)
    messages = result.scalars().all()
    
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "What is the password policy?"
    
    assert messages[1].role == "assistant"
    assert messages[1].content == data["answer"]
    assert messages[1].prompt_tokens is not None
    assert len(messages[1].citations) > 0
    assert messages[1].citations[0]["chunk_id"] == str(chunk_a.id)
    
    # 3. Security Test: User B tries to access Conversation A
    token_b = token_factory(user_b.id)
    response_b = await async_client.post(
        "/api/v1/chat/",
        json={"query": "I am user B hacking", "conversation_id": conversation_id},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response_b.status_code == 404

    # 4. Context Window & History Logic
    # Send another message to same conversation
    response2 = await async_client.post(
        "/api/v1/chat/",
        json={"query": "And what else?", "conversation_id": conversation_id},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response2.status_code == 200
    
    # Check that messages grew to 4
    result = await db_session.execute(stmt)
    messages = result.scalars().all()
    assert len(messages) == 4
