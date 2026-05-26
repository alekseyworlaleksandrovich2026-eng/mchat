from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.knowledge.chunking import ChunkConfig, chunk_text
from app.knowledge.importer import DocumentImporter
from app.models.knowledge import Document, KnowledgeBase
from app.schemas.knowledge import DocumentCreate
from app.services.knowledge_service import KnowledgeService


class _FakeEmbedder:
    def is_configured(self) -> bool:
        return True

    async def embed_documents(self, chunks: list[str]) -> list[list[float]]:
        return [[0.1] * 768 for _ in chunks]


def _noop_validate_dimension(self, dim: int) -> None:
    return None


def _patch_importer_embedder(monkeypatch) -> None:
    monkeypatch.setattr("app.knowledge.importer.milvus_client._connected", True)
    monkeypatch.setattr(
        DocumentImporter,
        "_validate_embedding_dimension",
        _noop_validate_dimension,
    )
    monkeypatch.setattr(
        "app.knowledge.importer.embedder_for_config",
        lambda _cfg: _FakeEmbedder(),
    )


@pytest.mark.asyncio
async def test_index_document_passes_user_id_to_milvus(monkeypatch):
    _patch_importer_embedder(monkeypatch)
    importer = DocumentImporter()
    importer._embedder = _FakeEmbedder()
    doc = Document(
        id="doc-1",
        knowledge_base_id="kb-1",
        title="Manual",
        content="Alpha paragraph.\n\nBeta paragraph.",
        source="manual",
    )
    captured: dict[str, object] = {}

    _patch_importer_embedder(monkeypatch)

    async def fake_insert_vectors(**kwargs):
        captured.update(kwargs)
        return len(kwargs["chunks"])

    monkeypatch.setattr(
        "app.knowledge.importer.milvus_client.insert_vectors", fake_insert_vectors
    )

    chunk_count = await importer.index_document(doc, user_id="user-123")

    assert chunk_count > 0
    assert captured["user_id"] == "user-123"
    assert captured["kb_id"] == "kb-1"
    assert captured["document_id"] == "doc-1"


@pytest.mark.asyncio
async def test_import_file_assigns_document_id_before_indexing(monkeypatch, tmp_path: Path):
    _patch_importer_embedder(monkeypatch)
    importer = DocumentImporter()
    importer._embedder = _FakeEmbedder()
    file_path = tmp_path / "notes.txt"
    file_path.write_text("Hello knowledge base", encoding="utf-8")

    captured: dict[str, object] = {}

    _patch_importer_embedder(monkeypatch)

    async def fake_insert_vectors(**kwargs):
        captured.update(kwargs)
        return len(kwargs["chunks"])

    monkeypatch.setattr(
        "app.knowledge.importer.milvus_client.insert_vectors", fake_insert_vectors
    )

    doc = await importer.import_file(
        kb_id="kb-42",
        user_id="user-42",
        file_path=file_path,
        original_filename="notes.txt",
    )

    assert doc.id
    assert captured["document_id"] == doc.id
    assert captured["kb_id"] == "kb-42"
    assert captured["user_id"] == "user-42"
    assert doc.status == "indexed"
    assert doc.chunk_count == 1


def test_chunk_text_short_document_returns_single_chunk():
    chunks = chunk_text("short note", ChunkConfig(strategy="fixed", size=500, overlap=0))
    assert len(chunks) == 1
    assert chunks[0] == "short note"


@pytest.mark.asyncio
async def test_create_document_passes_kb_user_id_to_indexer(db_session, monkeypatch):
    kb = KnowledgeBase(user_id="owner-1", name="KB")
    db_session.add(kb)
    await db_session.flush()

    captured: dict[str, object] = {}

    async def fake_index_document(self, doc: Document, *, user_id: str) -> int:
        captured["doc_id"] = doc.id
        captured["user_id"] = user_id
        return 2

    monkeypatch.setattr(DocumentImporter, "index_document", fake_index_document)

    service = KnowledgeService(db_session)
    response = await service.create_document(
        kb_id=kb.id,
        user_id=kb.user_id,
        data=DocumentCreate(title="Guide", content="Hello world"),
    )

    assert response.status == "indexed"
    assert response.chunk_count == 2
    assert captured["user_id"] == kb.user_id
    assert captured["doc_id"] == response.id


@pytest.mark.asyncio
async def test_import_file_and_url_pass_kb_user_id(db_session, monkeypatch, tmp_path: Path):
    kb = KnowledgeBase(user_id="owner-2", name="KB")
    db_session.add(kb)
    await db_session.flush()

    file_call: dict[str, object] = {}
    url_call: dict[str, object] = {}

    async def fake_import_file(
        self,
        kb_id: str,
        user_id: str,
        file_path: Path,
        original_filename: str,
        kb: KnowledgeBase | None = None,
    ) -> Document:
        file_call.update(
            {
                "kb_id": kb_id,
                "user_id": user_id,
                "file_path": file_path,
                "original_filename": original_filename,
            }
        )
        return Document(
            knowledge_base_id=kb_id,
            title=original_filename,
            content="file body",
            source="txt",
            status="indexed",
            chunk_count=1,
        )

    async def fake_import_url(
        self,
        kb_id: str,
        user_id: str,
        url: str,
        kb: KnowledgeBase | None = None,
    ) -> Document:
        url_call.update({"kb_id": kb_id, "user_id": user_id, "url": url})
        return Document(
            knowledge_base_id=kb_id,
            title=url,
            content="url body",
            source="url",
            source_url=url,
            status="indexed",
            chunk_count=1,
        )

    monkeypatch.setattr(DocumentImporter, "import_file", fake_import_file)
    monkeypatch.setattr(DocumentImporter, "import_url", fake_import_url)

    service = KnowledgeService(db_session)
    upload = UploadFile(filename="notes.txt", file=io.BytesIO(b"hello"))

    await service.import_file(kb_id=kb.id, user_id=kb.user_id, file=upload)
    await service.import_url(
        kb_id=kb.id,
        user_id=kb.user_id,
        url="https://example.com/help",
    )

    assert file_call["kb_id"] == kb.id
    assert file_call["user_id"] == kb.user_id
    assert file_call["original_filename"] == "notes.txt"
    assert url_call == {
        "kb_id": kb.id,
        "user_id": kb.user_id,
        "url": "https://example.com/help",
    }
