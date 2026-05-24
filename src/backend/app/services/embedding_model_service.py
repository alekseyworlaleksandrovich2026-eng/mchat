"""Upload and manage local embedding model files."""

from __future__ import annotations

import shutil
import uuid
import zipfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from loguru import logger

from app.core.config import settings
from app.knowledge.model_storage import embedding_model_storage_path, embedding_models_root
from app.models.embedding_model import EmbeddingModel
from app.schemas.embedding_model import EmbeddingModelResponse

# Files that indicate a HuggingFace / sentence-transformers layout
_MODEL_MARKERS = frozenset(
    {
        "config.json",
        "modules.json",
        "pytorch_model.bin",
        "model.safetensors",
        "tokenizer.json",
        "sentence_bert_config.json",
    }
)


def _validate_model_dir(path: Path) -> None:
    if not path.is_dir():
        raise ValueError("模型目录无效")
    names = {p.name for p in path.rglob("*") if p.is_file()}
    if not names & _MODEL_MARKERS:
        raise ValueError(
            "未识别为有效的 Embedding 模型包，需包含 config.json、"
            "model.safetensors 或 pytorch_model.bin 等文件"
        )


def _resolve_model_root(extract_dir: Path) -> Path:
    """If zip has a single top-level folder, use it as model root."""
    entries = [p for p in extract_dir.iterdir() if p.name != "__MACOSX"]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return extract_dir


def _safe_extract_zip(zip_path: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            member_path = Path(member)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError("压缩包包含非法路径")
            target = (dest / member).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise ValueError("压缩包路径越界")
        archive.extractall(dest)


class EmbeddingModelService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_models(self, user_id: str) -> list[EmbeddingModelResponse]:
        result = await self.db.execute(
            select(EmbeddingModel)
            .where(EmbeddingModel.user_id == user_id)
            .order_by(EmbeddingModel.created_at.desc())
        )
        return [
            EmbeddingModelResponse.model_validate(row)
            for row in result.scalars().all()
        ]

    async def get_model(
        self, model_id: str, user_id: str
    ) -> EmbeddingModel | None:
        result = await self.db.execute(
            select(EmbeddingModel).where(
                EmbeddingModel.id == model_id,
                EmbeddingModel.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def upload_model(
        self, user_id: str, file: UploadFile, name: str | None = None
    ) -> EmbeddingModelResponse:
        filename = (file.filename or "model.zip").lower()
        if not filename.endswith(".zip"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请上传 .zip 格式的模型包（HuggingFace / sentence-transformers 目录打包）",
            )

        raw = await file.read()
        max_bytes = settings.embedding_model_max_mb * 1024 * 1024
        if len(raw) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"模型包超过大小限制（{settings.embedding_model_max_mb} MB）",
            )

        model_id = str(uuid.uuid4())
        display_name = (name or Path(file.filename or "model").stem).strip() or "本地模型"
        dest = embedding_model_storage_path(model_id)
        tmp_zip = dest.parent / f"{model_id}.upload.zip"

        record = EmbeddingModel(
            id=model_id,
            user_id=user_id,
            name=display_name,
            status="processing",
            file_size=len(raw),
        )
        self.db.add(record)
        await self.db.flush()

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp_zip.write_bytes(raw)
            extract_staging = dest.parent / f"{model_id}.staging"
            if extract_staging.exists():
                shutil.rmtree(extract_staging)
            _safe_extract_zip(tmp_zip, extract_staging)
            model_root = _resolve_model_root(extract_staging)
            _validate_model_dir(model_root)

            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(model_root), str(dest))
            shutil.rmtree(extract_staging, ignore_errors=True)

            from app.knowledge.local_embedder import probe_model_dimension

            dimension = await self._probe_dimension(dest)
            record.dimension = dimension
            record.status = "ready"
            record.error_message = None
        except Exception as exc:
            record.status = "failed"
            record.error_message = str(exc)
            shutil.rmtree(dest, ignore_errors=True)
            logger.error(f"Embedding model upload failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"模型加载失败: {exc}",
            ) from exc
        finally:
            tmp_zip.unlink(missing_ok=True)
            await self.db.flush()
            await self.db.refresh(record)

        return EmbeddingModelResponse.model_validate(record)

    async def _probe_dimension(self, model_dir: Path) -> int:
        import asyncio

        from app.knowledge.local_embedder import probe_model_dimension

        return await asyncio.to_thread(probe_model_dimension, model_dir)

    async def delete_model(self, model_id: str, user_id: str) -> bool:
        record = await self.get_model(model_id, user_id)
        if record is None:
            return False

        from app.models.knowledge import KnowledgeBase

        in_use = await self.db.execute(
            select(KnowledgeBase.id).where(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.embedding_provider == "local",
                KnowledgeBase.embedding_model == model_id,
            )
        )
        if in_use.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="仍有知识库绑定此本地模型，请先在 RAG 设置中更换后再删除",
            )

        from app.knowledge.local_embedder import unload_model

        unload_model(model_id)
        shutil.rmtree(embedding_model_storage_path(model_id), ignore_errors=True)
        await self.db.delete(record)
        await self.db.flush()
        return True
