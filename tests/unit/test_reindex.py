import pytest

from app.knowledge.embedding_fingerprint import embedding_fingerprint, needs_reindex
from app.knowledge.importer import DocumentImporter
from app.models.knowledge import Document, KnowledgeBase
from app.models.user import User
from app.schemas.knowledge import ReindexRequest
from app.services.knowledge_service import KnowledgeService


def test_needs_reindex_when_embedding_changes():
    kb = KnowledgeBase(
        user_id="u1",
        name="KB",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_dimension=1536,
        indexed_embedding_key="openai|text-embedding-3-large|1536|",
    )
    assert needs_reindex(kb) is True

    kb.embedding_model = "text-embedding-3-small"
    kb.indexed_embedding_key = embedding_fingerprint(kb)
    assert needs_reindex(kb) is False


@pytest.mark.asyncio
async def test_reindex_knowledge_base(db_session, monkeypatch):
    user = User(username="reindex_admin", password_hash="hash", role="admin")
    db_session.add(user)
    await db_session.flush()

    kb = KnowledgeBase(
        user_id=user.id,
        name="Reindex KB",
        indexed_embedding_key="openai|old-model|1536|",
    )
    db_session.add(kb)
    await db_session.flush()

    doc = Document(
        knowledge_base_id=kb.id,
        title="Doc",
        content="一些测试内容用于重嵌入。",
        status="indexed",
        chunk_count=1,
    )
    db_session.add(doc)
    await db_session.commit()

    async def fake_reindex(self, document, *, user_id, rechunk=True):
        document.status = "indexed"
        document.chunk_count = 2
        return 2

    async def fake_mark(self, knowledge_base):
        knowledge_base.indexed_embedding_key = embedding_fingerprint(knowledge_base)

    monkeypatch.setattr(DocumentImporter, "reindex_document", fake_reindex)
    monkeypatch.setattr(DocumentImporter, "mark_kb_indexed", fake_mark)

    service = KnowledgeService(db_session)
    result = await service.reindex_knowledge_base(
        kb.id, user.id, ReindexRequest(rechunk=True)
    )

    assert result.total == 1
    assert result.succeeded == 1
    await db_session.refresh(kb)
    assert kb.reindex_status == "completed"
    # After reindex, fingerprint should match current KB embedding config
    kb.indexed_embedding_key = embedding_fingerprint(kb)
    assert needs_reindex(kb) is False
