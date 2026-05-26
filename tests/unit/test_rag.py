import pytest

from app.knowledge.rag import RagService
from app.models.knowledge import Document, KnowledgeBase
from app.models.user import User
from tests.conftest import TestSessionFactory


@pytest.mark.asyncio
async def test_vector_search_uses_document_title_from_database(db_session, monkeypatch):
    user = User(username='rag_admin', password_hash='hash', role='admin')
    db_session.add(user)
    await db_session.flush()

    knowledge_base = KnowledgeBase(user_id=user.id, name='Support KB')
    db_session.add(knowledge_base)
    await db_session.flush()

    document = Document(
        knowledge_base_id=knowledge_base.id,
        title='安装手册',
        content='这是安装步骤。',
        status='indexed',
        chunk_count=3,
    )
    db_session.add(document)
    await db_session.commit()

    class FakeEmbedder:
        def is_configured(self) -> bool:
            return True

        async def embed_query(self, _query: str):
            return [0.12, 0.34, 0.56]

    async def fake_search(**_kwargs):
        return [
            {
                'document_id': document.id,
                'kb_id': knowledge_base.id,
                'chunk_index': 2,
                'content': '这是安装步骤。',
                'distance': 0.91,
            }
        ]

    monkeypatch.setattr('app.core.database.async_session_factory', TestSessionFactory)
    monkeypatch.setattr(
        'app.knowledge.rag.embedder_for_config',
        lambda _cfg: FakeEmbedder(),
    )
    monkeypatch.setattr('app.knowledge.rag.milvus_client.search', fake_search)
    monkeypatch.setattr('app.knowledge.rag.milvus_client._connected', True)

    response = await RagService().search(
        query='安装怎么做',
        user_id=user.id,
        knowledge_base_id=knowledge_base.id,
        top_k=3,
    )

    assert response.total == 1
    assert response.results[0].document_id == document.id
    assert response.results[0].title == '安装手册'