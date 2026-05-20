"""Knowledge base API router."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_admin
from app.models.user import User
from app.schemas.knowledge import (
    DocumentCreate,
    DocumentListItem,
    DocumentResponse,
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


@router.post("/bases", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    request: KnowledgeBaseCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base."""
    service = KnowledgeService(db)
    return await service.create_knowledge_base(
        user_id=admin.id, data=request
    )


@router.get("/bases", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all knowledge bases for current user."""
    service = KnowledgeService(db)
    return await service.list_knowledge_bases(user_id=admin.id)


@router.get("/bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific knowledge base."""
    service = KnowledgeService(db)
    kb = await service.get_knowledge_base(
        kb_id=kb_id, user_id=admin.id
    )
    if kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )
    return kb


@router.delete("/bases/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a knowledge base."""
    service = KnowledgeService(db)
    success = await service.delete_knowledge_base(
        kb_id=kb_id, user_id=admin.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )
    return None


@router.get("/bases/{kb_id}/documents", response_model=list[DocumentListItem])
async def list_documents(
    kb_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all documents in a knowledge base."""
    service = KnowledgeService(db)
    return await service.list_documents(
        kb_id=kb_id, user_id=admin.id
    )


@router.post("/bases/{kb_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    kb_id: str,
    request: DocumentCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a document to a knowledge base and index it."""
    service = KnowledgeService(db)
    return await service.create_document(
        kb_id=kb_id, user_id=admin.id, data=request
    )


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    service = KnowledgeService(db)
    success = await service.delete_document(
        doc_id=doc_id, user_id=admin.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return None


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Search documents using semantic search."""
    service = KnowledgeService(db)
    return await service.search(
        query=request.query,
        user_id=admin.id,
        knowledge_base_id=request.knowledge_base_id,
        top_k=request.top_k,
    )


@router.post("/bases/{kb_id}/import-file", response_model=DocumentListItem)
async def import_file(
    kb_id: str,
    file: UploadFile,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import a file into a knowledge base."""
    service = KnowledgeService(db)
    try:
        doc = await service.import_file(
            kb_id=kb_id,
            user_id=admin.id,
            file=file,
        )
        return doc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import failed: {e}",
        )


@router.post("/bases/{kb_id}/import-url")
async def import_url(
    kb_id: str,
    url: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import content from a URL into a knowledge base."""
    service = KnowledgeService(db)
    try:
        doc = await service.import_url(
            kb_id=kb_id,
            user_id=admin.id,
            url=url,
        )
        return doc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL import failed: {e}",
        )
