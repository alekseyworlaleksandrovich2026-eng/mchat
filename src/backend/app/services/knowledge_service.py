"""Knowledge service - business logic for knowledge management."""

import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.importer import DocumentImporter
from app.knowledge.rag import RagService
from app.models.knowledge import Document, KnowledgeBase
from app.services.storage_service import storage_service
from app.schemas.knowledge import (
    DocumentCreate,
    DocumentListItem,
    DocumentResponse,
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    SearchResponse,
)


def _kb_to_response(kb: KnowledgeBase) -> KnowledgeBaseResponse:
    return KnowledgeBaseResponse(
        id=kb.id,
        user_id=kb.user_id,
        name=kb.name,
        description=kb.description,
        enabled=kb.enabled,
        document_count=len(kb.documents) if kb.documents is not None else 0,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


def _doc_to_list_item(doc: Document) -> DocumentListItem:
    return DocumentListItem(
        id=doc.id,
        knowledge_base_id=doc.knowledge_base_id,
        title=doc.title,
        source=doc.source,
        status=doc.status,
        chunk_count=doc.chunk_count,
        file_size=len(doc.content or ""),
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


class KnowledgeService:
    """Handles knowledge base business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_knowledge_base(
        self, user_id: str, data: KnowledgeBaseCreate
    ) -> KnowledgeBaseResponse:
        """Create a new knowledge base."""
        kb = KnowledgeBase(
            user_id=user_id,
            name=data.name,
            description=data.description,
            enabled=data.enabled,
        )
        self.db.add(kb)
        await self.db.flush()
        await self.db.refresh(kb)
        return _kb_to_response(kb)

    async def list_knowledge_bases(
        self, user_id: str
    ) -> list[KnowledgeBaseResponse]:
        """List all knowledge bases for a user."""
        result = await self.db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.user_id == user_id)
            .order_by(KnowledgeBase.created_at.desc())
        )
        kbs = result.scalars().all()
        return [_kb_to_response(kb) for kb in kbs]

    async def get_knowledge_base(
        self, kb_id: str, user_id: str
    ) -> KnowledgeBaseResponse | None:
        """Get a specific knowledge base."""
        result = await self.db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.user_id == user_id,
            )
        )
        kb = result.scalar_one_or_none()
        if kb is None:
            return None
        return _kb_to_response(kb)

    async def delete_knowledge_base(
        self, kb_id: str, user_id: str
    ) -> bool:
        """Delete a knowledge base and its documents."""
        result = await self.db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.user_id == user_id,
            )
        )
        kb = result.scalar_one_or_none()
        if kb is None:
            return False
        await self.db.delete(kb)
        await self.db.flush()
        return True

    async def list_documents(
        self, kb_id: str, user_id: str
    ) -> list[DocumentListItem]:
        """List all documents in a knowledge base."""
        # Verify ownership
        kb_result = await self.db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.user_id == user_id,
            )
        )
        if kb_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found",
            )

        result = await self.db.execute(
            select(Document)
            .where(Document.knowledge_base_id == kb_id)
            .order_by(Document.created_at.desc())
        )
        docs = result.scalars().all()
        return [_doc_to_list_item(d) for d in docs]

    async def create_document(
        self, kb_id: str, user_id: str, data: DocumentCreate
    ) -> DocumentResponse:
        """Create a document and index it."""
        # Verify ownership
        kb_result = await self.db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.user_id == user_id,
            )
        )
        kb = kb_result.scalar_one_or_none()
        if kb is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found",
            )

        # Create document record
        doc = Document(
            knowledge_base_id=kb_id,
            title=data.title,
            content=data.content,
            source=data.source or "manual",
            source_url=data.source_url,
            status="pending",
        )
        self.db.add(doc)
        await self.db.flush()

        # Index in Milvus
        try:
            importer = DocumentImporter()
            chunk_count = await importer.index_document(doc, user_id=kb.user_id)
            doc.status = "indexed"
            doc.chunk_count = chunk_count
        except Exception:
            doc.status = "failed"

        await self.db.flush()
        await self.db.refresh(doc)
        return DocumentResponse.model_validate(doc)

    async def delete_document(
        self, doc_id: str, user_id: str
    ) -> bool:
        """Delete a document."""
        # Verify ownership through KB
        result = await self.db.execute(
            select(Document).join(KnowledgeBase).where(
                Document.id == doc_id,
                KnowledgeBase.user_id == user_id,
            )
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            return False
        await self.db.delete(doc)
        await self.db.flush()
        return True

    async def search(
        self,
        query: str,
        user_id: str,
        knowledge_base_id: str | None = None,
        top_k: int = 5,
    ) -> SearchResponse:
        """Search documents using semantic search."""
        rag = RagService()
        results = await rag.search(
            query=query,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            top_k=top_k,
        )
        return results

    async def import_file(
        self, kb_id: str, user_id: str, file: UploadFile
    ) -> DocumentListItem:
        """Import a file into a knowledge base."""
        # Verify ownership
        kb_result = await self.db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.user_id == user_id,
            )
        )
        kb = kb_result.scalar_one_or_none()
        if kb is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found",
            )

        content = await file.read()
        stored = storage_service.save_bytes(
            content,
            filename=file.filename or "upload.dat",
            content_type=file.content_type,
            prefix="knowledge",
        )

        temp_path: Path | None = None
        file_path = stored.local_path
        if file_path is None:
            suffix = Path(file.filename or "upload.dat").suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(content)
                temp_path = Path(f.name)
            file_path = temp_path

        # Import and index
        importer = DocumentImporter()
        try:
            doc = await importer.import_file(
                kb_id=kb_id,
                user_id=kb.user_id,
                file_path=file_path,
                original_filename=file.filename or "unknown",
            )
            doc.knowledge_base_id = kb_id
            self.db.add(doc)
            await self.db.flush()
            await self.db.refresh(doc)
            return _doc_to_list_item(doc)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to import file: {e}",
            )
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    async def import_url(
        self, kb_id: str, user_id: str, url: str
    ) -> DocumentResponse:
        """Import content from a URL."""
        # Verify ownership
        kb_result = await self.db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.user_id == user_id,
            )
        )
        kb = kb_result.scalar_one_or_none()
        if kb is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found",
            )

        importer = DocumentImporter()
        try:
            doc = await importer.import_url(
                kb_id=kb_id,
                user_id=kb.user_id,
                url=url,
            )
            doc.knowledge_base_id = kb_id
            self.db.add(doc)
            await self.db.flush()
            await self.db.refresh(doc)
            return DocumentResponse.model_validate(doc)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to import URL: {e}",
            )
