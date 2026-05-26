import pytest

from app.knowledge.chunking import ChunkConfig, chunk_text


def test_fixed_chunking_respects_size():
    text = "word " * 300
    cfg = ChunkConfig(strategy="fixed", size=200, overlap=20)
    chunks = chunk_text(text, cfg)
    assert len(chunks) >= 2
    max_len = cfg.size + cfg.overlap + 80
    assert all(len(c) <= max_len for c in chunks)


def test_paragraph_chunking_keeps_paragraphs():
    text = "第一段内容。" * 15 + "\n\n" + "第二段内容。" * 15 + "\n\n" + "第三段内容。" * 15
    chunks = chunk_text(
        text,
        ChunkConfig(strategy="paragraph", size=500, overlap=0, min_chunk_size=20),
    )
    joined = "\n".join(chunks)
    assert "第一段" in joined
    assert "第二段" in joined
    assert "第三段" in joined


def test_markdown_splits_on_headings():
    text = "# Title\n\nIntro paragraph.\n\n## Section\n\nDetails here."
    chunks = chunk_text(text, ChunkConfig(strategy="markdown", size=800))
    assert any("Title" in c for c in chunks)
    assert any("Section" in c or "Details" in c for c in chunks)
