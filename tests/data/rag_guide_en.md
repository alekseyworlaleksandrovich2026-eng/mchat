# RAG System Configuration Guide

## Overview

Retrieval-Augmented Generation (RAG) combines information retrieval with large language models to produce accurate, context-aware responses. This guide covers the complete configuration workflow.

## Embedding Configuration

### Provider Options

1. **Ollama (Local)**
   - No API key required
   - Recommended model: `nomic-embed-text` (768 dimensions)
   - Setup: `ollama pull nomic-embed-text`

2. **OpenAI Compatible**
   - Requires API key
   - Default model: `text-embedding-ada-002` (1536 dimensions)
   - Supports any OpenAI-compatible endpoint

3. **Local Upload**
   - Upload a sentence-transformers model as a `.zip` file
   - Maximum file size: 2048 MB
   - Supports all HuggingFace sentence-transformers models

### Dimension Alignment

The embedding dimension must match across the entire Milvus collection. When you create your first knowledge base with a specific dimension, all subsequent knowledge bases must use the same dimension unless you manually reset the Milvus collection.

## Chunking Strategies

### Fixed Size Chunking
- Splits text by character count
- Configurable size (100-4000) and overlap (0-500)
- Best for: General purpose text

### Paragraph Chunking
- Splits by paragraph boundaries (double newlines)
- Merges small paragraphs to meet minimum size
- Best for: Well-structured documents, articles

### Markdown Chunking
- Splits by heading sections (H1-H6)
- Preserves document structure
- Best for: Technical documentation, README files

### Semantic Chunking
- Uses embedding similarity to detect topic boundaries
- Generates parent-child chunks for context enrichment
- Best for: Long-form content, books, research papers

## Retrieval Modes

1. **Vector Search**: Pure semantic similarity using cosine distance
2. **Keyword Search**: BM25-based exact matching with configurable parameters (k1, b)
3. **Hybrid Search**: Combines vector and keyword results using Reciprocal Rank Fusion (RRF)

## Reranking

After initial retrieval, results can be reranked for better relevance:

- **Lexical**: Lightweight keyword overlap scoring (no external API needed)
- **Cohere**: Cloud-based semantic reranking using Cohere's API
- **BGE**: Local reranking using BGE reranker models
- **None**: Skip reranking entirely

## Performance Tuning

### Recommended Settings

| Scenario | Chunk Size | Overlap | Top K | Rerank |
|----------|------------|---------|-------|--------|
| FAQ / Short Q&A | 300 | 50 | 5 | Lexical |
| Technical Docs | 500 | 100 | 5 | BGE |
| Long Articles | 800 | 150 | 10 | Cohere |
| Code Documentation | 1000 | 200 | 10 | Lexical |

### Query Rewriting

Enable query rewriting to automatically generate multiple search queries from a single user query. This improves recall for ambiguous or complex questions.

## Monitoring

MChat provides retrieval observability through:
- Search query logging with hit counts
- Duration tracking for each retrieval
- Zero-result detection and alerting
- Per-knowledge-base statistics dashboard
