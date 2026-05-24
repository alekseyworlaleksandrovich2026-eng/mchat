import pytest

from app.knowledge.chunking import ChunkConfig, chunk_text


def test_fixed_chunking_respects_size():
    text = "word " * 300
    chunks = chunk_text(text, ChunkConfig(strategy="fixed", size=200, overlap=20))
    assert len(chunks) >= 2
    assert all(len(c) <= 220 for c in chunks)


def test_paragraph_chunking_keeps_paragraphs():
    text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
    chunks = chunk_text(
        text, ChunkConfig(strategy="paragraph", size=500, overlap=0)
    )
    assert len(chunks) == 3
    assert "第一段" in chunks[0]


def test_markdown_splits_on_headings():
    text = "# Title\n\nIntro paragraph.\n\n## Section\n\nDetails here."
    chunks = chunk_text(text, ChunkConfig(strategy="markdown", size=800))
    assert any("Title" in c for c in chunks)
    assert any("Section" in c or "Details" in c for c in chunks)
