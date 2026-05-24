# Knowledge Base and Auto-Sent Assets

## The difference between the two features

### 1. Knowledge base

The knowledge base gives the AI retrieval context.

Flow:

1. The user sends a message.
2. The system searches the knowledge bases bound to the current customer agent.
3. Matching text chunks are appended to the system prompt.
4. The AI generates a natural-language answer based on those chunks.

The knowledge base helps the AI answer. It does not directly send files to the user.

### 2. Auto-sent assets

Auto-sent assets are configured separately on the customer agent.

Typical use cases:

- When a user asks for a manual, automatically attach a PDF
- When a user asks for a demo video, automatically attach a video
- When a user asks for installation instructions, automatically attach a link

This flow runs in parallel with the knowledge base instead of replacing it.
## Current implementation

The customer agent now supports auto-sent asset rules.

Each rule includes:

- Rule name
- Trigger description
- Optional keywords
- Optional reply note
- Asset file or asset URL
- Optional channel restrictions

Runtime flow:

1. The user sends a message.
2. The system matches auto-sent rules by keyword and semantic similarity.
3. When a rule matches, the asset is attached as an outbound assistant asset.
4. If a reply note is configured, it is appended to the response text.
5. Matched rules are stored in message metadata and can be shown in the chat history.
## How the knowledge base is triggered

The knowledge base is only used when:

1. The current conversation is bound to a customer agent.
2. That customer agent has at least one knowledge base selected.
3. The user question is relevant to stored knowledge chunks.

Current semantics:

- Only selected knowledge bases are used
- If none are selected, the knowledge base is disabled

There is no longer any fallback logic where an empty selection means all knowledge bases.
## How models are involved

Two model types matter here:

### 1. Chat model

The chat model is responsible for the final answer.

It mainly affects:

- Answer quality
- Tool-calling ability
- Summarization and expression

### 2. Embedding model

The embedding model powers vectorization and semantic retrieval.

It mainly affects:

- Knowledge-base hit quality
- Semantic matching for auto-sent asset rules

If the problem is poor writing or weak reasoning, look at the chat model first.

If the problem is that documents exist but are not retrieved, look at the embedding model and chunking strategy first.
## The full knowledge-base pipeline

From upload to answer, the knowledge base usually goes through 6 steps:

1. Upload the document. Supported examples include txt and docx.
2. Parse the document into plain text.
3. Split long text into chunks.
4. Convert each chunk into embeddings.
5. Store vectors in Milvus. If Milvus is unavailable, query-time fallback uses database keyword search.
6. At chat time, retrieve relevant chunks and append them to the system prompt so the chat model can answer.

So the knowledge base does not send an entire document as-is. It retrieves relevant parts and lets the AI turn them into an answer.
## Example 1: product specification Q&A

Suppose the knowledge base contains:

- Title: X100 Device Specification
- Content: battery life, charging time, working temperature, connector type

User question:

- "How long can the X100 run continuously?"

What happens:

1. The system searches for relevant chunks.
2. It finds the chunk that says battery life is 8 hours.
3. That chunk is added to the system prompt.
4. The AI answers with something like: "Under standard conditions, the X100 can run for about 8 hours."

The user receives an answer, not a file attachment.
## Example 2: after-sales policy Q&A

Suppose the knowledge base contains a policy that says:

- Returns are allowed within 7 days after delivery; warranty is 1 year; human-caused damage is excluded.

User question:

- "Can I return this product?"

The system retrieves the return-policy chunk and the AI can answer more naturally, for example:

- "Yes. Returns are supported within 7 days after delivery. After that, warranty terms apply."

Without a knowledge base, the AI may guess. With a knowledge base, the answer is grounded in your own business policy.
## Example 3: knowledge base and auto-sent assets together

A common support setup is:

- Put the installation guide text in the knowledge base
- Put the installation PDF in an auto-sent asset rule

User question:

- "How do I install it? Also send me the installation document."

Two things can happen at the same time:

1. The knowledge base hits installation steps and the AI explains them in text.
2. The auto-sent asset rule hits the request for the installation document and attaches the PDF.

The user gets both the explanation and the file.
## Recommended setup

### Good fit for the knowledge base

- FAQs
- Product descriptions
- Policy terms
- Long-form text documents

### Good fit for auto-sent assets

- PDF manuals
- Product brochures
- Demo videos
- Download links
- Service forms

### Practical advice

1. Put answerable text knowledge into the knowledge base.
2. Put user-deliverable files and videos into auto-sent asset rules.
3. Write trigger descriptions using real user language instead of internal labels.
4. Keep each rule focused on one main asset type.
5. If a question needs both an answer and a file, use both features together.
## Troubleshooting checklist

If a document was uploaded and vectorized but the answer still does not use it, check these items in order:

1. Is the knowledge base actually selected on the current customer agent?
2. Did the document import succeed instead of ending in failed status?
3. Does the document content contain the relevant text, not only a related filename?
4. Is the user question too short or too colloquial for strong retrieval signals?
5. Is Milvus available? If not, the fallback keyword search is usually weaker than vector retrieval.
6. Is the embedding model suitable for your language mix and domain?

A useful rule of thumb is:

- Put directly answerable text into the knowledge base
- Put files, videos, and delivery links into auto-sent asset rules

That split keeps the trigger path much clearer.

## Current limits and planned improvements

Below is the **current state** of the knowledge base / RAG pipeline in code (see [roadmap.en.md](roadmap.en.md) for the full product plan).

### Current (implemented)

| Area | Behavior |
|------|----------|
| Chunking | Per-KB `fixed` / `paragraph` / `markdown` / `semantic`, configurable size / overlap / min_chunk / semantic_threshold |
| Embedding | Per-KB provider / model / api_base / dimension; global `.env` as default; local zip upload + Ollama |
| Retrieval | `vector` / `keyword` / `hybrid`; hybrid uses RRF to fuse vector + BM25 keyword results |
| Rerank | `lexical` (built-in) / `cohere` / `bge` / `cross-encoder`, configurable provider / model / top_n |
| Query rewriting | LLM-based multi-perspective queries (on/off switch), multi-query results merged via RRF |
| Parent-child | Semantic strategy auto-generates parent context; child hits enriched with parent content |
| Storage | `document_chunks` table (with `parent_content`) + Milvus vector store |
| Reindex | Per-KB `POST .../reindex`, `reindex_status` progress tracking, `indexed_embedding_key` fingerprint |

Admin UI: Knowledge Base → **RAG Settings**. API: `PATCH /api/knowledge/bases/{id}`.

### Local embedding model upload

Upload a [sentence-transformers](https://www.sbert.net/) / HuggingFace model directory as **zip**:

1. Admin panel **Knowledge Base** page top → **Upload model zip**
2. After validation, in **RAG Settings** set provider to **Local uploaded model** and select the model
3. Set **Vector dimension** to the model's output dimension (auto-filled on model selection)
4. Run **Full re-embed**

Dependency (backend):

```bash
pip install sentence-transformers
```

API:
- `GET /api/knowledge/embedding-models` — list
- `POST /api/knowledge/embedding-models/upload` — upload zip
- `DELETE /api/knowledge/embedding-models/{id}` — delete

**Ollama** is also supported (`embedding_provider=ollama`, no upload needed, requires local Ollama running).

### Full re-embed

After switching embedding (or optionally chunking strategy):

1. Save RAG settings
2. Click **Full re-embed** at the bottom of **RAG Settings**
3. Optionally check **Re-chunk with current strategy**

API: `POST /api/knowledge/bases/{id}/reindex`, body: `{ "rechunk": true }`.

The system records `indexed_embedding_key`; when config differs from fingerprint, the list shows **Reindex needed**.

### Further planned

- Async background reindex with real-time progress
- Retrieval observability logs & zero-result analysis
- Eval dataset (Q&A pairs + Recall@k / MRR)
- A/B retrieval comparison

See [product roadmap](roadmap.en.md#1-knowledge-base--rag).