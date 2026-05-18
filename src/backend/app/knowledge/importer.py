"""Document import - parse files, chunk, embed, store."""

from __future__ import annotations

from pathlib import Path

import httpx
from loguru import logger

from app.knowledge.embedder import embedder
from app.knowledge.milvus_client import milvus_client
from app.models.knowledge import Document


class DocumentImporter:
    """Import documents, chunk them, generate embeddings, and store in Milvus."""

    CHUNK_SIZE = 500  # characters per chunk
    CHUNK_OVERLAP = 50

    async def import_file(
        self,
        kb_id: str,
        file_path: Path,
        original_filename: str,
    ) -> Document:
        """Import a file as a knowledge document."""
        content = await self._read_file(file_path)
        source = file_path.suffix.lower().lstrip(".")

        doc = Document(
            knowledge_base_id=kb_id,
            title=original_filename,
            content=content,
            source=source,
            status="processing",
        )

        chunks = self._chunk_text(content)
        if not content.strip():
            doc.status = "failed"
            doc.chunk_count = 0
            return doc

        if not milvus_client._connected:
            doc.chunk_count = len(chunks)
            doc.status = "indexed"
            logger.info(
                f"Document {doc.title} stored in DB ({len(chunks)} chunks); "
                "Milvus disabled — keyword search available"
            )
            return doc

        chunk_count = await self.index_document(doc)
        doc.chunk_count = chunk_count
        doc.status = "indexed" if chunk_count > 0 else "failed"

        return doc

    async def import_url(self, kb_id: str, url: str) -> Document:
        """Import content from a URL."""
        try:
            async with httpx.AsyncClient(
                timeout=30.0, follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                content = response.text

            doc = Document(
                knowledge_base_id=kb_id,
                title=url,
                content=content,
                source="url",
                source_url=url,
                status="processing",
            )

            if not milvus_client._connected:
                chunks = self._chunk_text(content)
                doc.chunk_count = len(chunks)
                doc.status = "indexed" if content.strip() else "failed"
                return doc

            chunk_count = await self.index_document(doc)
            doc.chunk_count = chunk_count
            doc.status = "indexed" if chunk_count > 0 else "failed"

            return doc
        except Exception as e:
            logger.error(f"URL import failed for {url}: {e}")
            raise

    async def index_document(self, doc: Document) -> int:
        """Chunk and index a document's content into Milvus."""
        # Skip if Milvus is not enabled
        if not milvus_client._connected:
            logger.warning("Milvus not connected, skipping indexing")
            return 0

        try:
            chunks = self._chunk_text(doc.content)
            if not chunks:
                return 0

            # Generate embeddings for chunks
            embeddings = await embedder.embed_documents(chunks)

            # Insert into Milvus
            chunk_count = await milvus_client.insert_vectors(
                document_id=doc.id,
                kb_id=doc.knowledge_base_id,
                user_id="",  # Will be set by caller
                chunks=chunks,
                embeddings=embeddings,
            )

            logger.info(
                f"Indexed document {doc.id}: {chunk_count} chunks"
            )
            return chunk_count
        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            raise

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []

        # Clean text
        text = text.strip()

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.CHUNK_SIZE, text_len)

            # Try to break at a natural boundary
            if end < text_len:
                # Look for paragraph break
                paragraph_break = text.rfind("\n\n", start, end)
                if paragraph_break > start:
                    end = paragraph_break + 2
                else:
                    # Look for sentence break
                    for sep in [". ", "! ", "? ", ".\n", "\n"]:
                        pos = text.rfind(sep, start, end)
                        if pos > start:
                            end = pos + len(sep)
                            break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.CHUNK_OVERLAP
            if start < 0:
                start = 0

        return chunks

    async def _read_file(self, file_path: Path) -> str:
        """Read file content based on extension."""
        suffix = file_path.suffix.lower()

        if suffix == ".txt":
            return file_path.read_text(encoding="utf-8", errors="replace")
        elif suffix == ".md":
            return file_path.read_text(encoding="utf-8", errors="replace")
        elif suffix == ".html" or suffix == ".htm":
            return file_path.read_text(encoding="utf-8", errors="replace")
        elif suffix == ".pdf":
            # Basic PDF text extraction fallback
            try:
                import pdfplumber

                with pdfplumber.open(file_path) as pdf:
                    pages = [page.extract_text() for page in pdf.pages]
                    return "\n\n".join(
                        p for p in pages if p
                    )
            except ImportError:
                logger.warning(
                    "pdfplumber not installed, returning placeholder"
                )
                return f"[PDF file: {file_path.name} - requires pdfplumber for parsing]"
        else:
            # Fallback: try reading as text
            return file_path.read_text(encoding="utf-8", errors="replace")
