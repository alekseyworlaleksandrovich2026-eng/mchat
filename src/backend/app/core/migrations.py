"""Lightweight schema patches for columns added after initial deploy."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from app.core.database import Base


def _column_names(conn: Connection, table: str) -> set[str]:
    insp = inspect(conn)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def apply_schema_patches(conn: Connection) -> list[str]:
    """Add missing columns on existing databases. Returns applied patch names."""
    applied: list[str] = []
    dialect = conn.dialect.name

    if "customer_configs" in inspect(conn).get_table_names():
        cols = _column_names(conn, "customer_configs")
        if "skill_ids" not in cols:
            if dialect == "mysql":
                conn.execute(
                    text(
                        "ALTER TABLE customer_configs "
                        "ADD COLUMN skill_ids JSON NULL"
                    )
                )
            else:
                conn.execute(
                    text(
                        "ALTER TABLE customer_configs "
                        "ADD COLUMN skill_ids TEXT NULL"
                    )
                )
            applied.append("customer_configs.skill_ids")
        if "knowledge_base_ids" not in cols:
            if dialect == "mysql":
                conn.execute(
                    text(
                        "ALTER TABLE customer_configs "
                        "ADD COLUMN knowledge_base_ids JSON NULL"
                    )
                )
            else:
                conn.execute(
                    text(
                        "ALTER TABLE customer_configs "
                        "ADD COLUMN knowledge_base_ids TEXT NULL"
                    )
                )
            applied.append("customer_configs.knowledge_base_ids")
        if "auto_reply_rules" not in cols:
            if dialect == "mysql":
                conn.execute(
                    text(
                        "ALTER TABLE customer_configs "
                        "ADD COLUMN auto_reply_rules JSON NULL"
                    )
                )
            else:
                conn.execute(
                    text(
                        "ALTER TABLE customer_configs "
                        "ADD COLUMN auto_reply_rules TEXT NULL"
                    )
                )
            applied.append("customer_configs.auto_reply_rules")
        if "widget_session_ttl_hours" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE customer_configs "
                    "ADD COLUMN widget_session_ttl_hours INTEGER NOT NULL DEFAULT 24"
                )
            )
            applied.append("customer_configs.widget_session_ttl_hours")
        if "short_code" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE customer_configs "
                    "ADD COLUMN short_code VARCHAR(32) NULL"
                )
            )
            try:
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX idx_customer_configs_short_code "
                        "ON customer_configs(short_code)"
                    )
                )
            except Exception:
                pass
            applied.append("customer_configs.short_code")

    # Expand users.role column for custom role names
    if "users" in inspect(conn).get_table_names():
        try:
            if dialect == "mysql":
                conn.execute(
                    text("ALTER TABLE users MODIFY COLUMN role VARCHAR(50) NOT NULL DEFAULT 'agent'")
                )
            elif dialect == "postgresql":
                conn.execute(
                    text("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50)")
                )
            applied.append("users.role_size")
        except Exception:
            pass

    if "conversations" in inspect(conn).get_table_names():
        cols = _column_names(conn, "conversations")
        if "client_ip" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE conversations "
                    "ADD COLUMN client_ip VARCHAR(64) NULL"
                )
            )
            applied.append("conversations.client_ip")
        if "customer_id" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE conversations "
                    "ADD COLUMN customer_id VARCHAR(36) NULL"
                )
            )
            applied.append("conversations.customer_id")
        # Create index separately (MySQL does not support IF NOT EXISTS)
        try:
            conn.execute(
                text(
                    "CREATE INDEX idx_conversations_customer_id "
                    "ON conversations(customer_id)"
                )
            )
        except Exception:
            pass

    if "knowledge_bases" in inspect(conn).get_table_names():
        cols = _column_names(conn, "knowledge_bases")
        kb_patches = [
            ("chunk_strategy", "VARCHAR(20) NOT NULL DEFAULT 'fixed'"),
            ("chunk_size", "INTEGER NOT NULL DEFAULT 500"),
            ("chunk_overlap", "INTEGER NOT NULL DEFAULT 50"),
            ("chunk_min_size", "INTEGER NOT NULL DEFAULT 80"),
            ("embedding_provider", "VARCHAR(50) NULL"),
            ("embedding_model", "VARCHAR(100) NULL"),
            ("embedding_api_base", "VARCHAR(500) NULL"),
            ("embedding_dimension", "INTEGER NOT NULL DEFAULT 1536"),
            ("retrieval_mode", "VARCHAR(20) NOT NULL DEFAULT 'hybrid'"),
            ("retrieval_top_k", "INTEGER NOT NULL DEFAULT 5"),
            ("retrieval_candidate_k", "INTEGER NOT NULL DEFAULT 20"),
            ("rerank_enabled", "BOOLEAN NOT NULL DEFAULT 1" if dialect == "mysql" else "BOOLEAN NOT NULL DEFAULT TRUE"),
            ("rerank_top_n", "INTEGER NOT NULL DEFAULT 5"),
            ("retrieval_bm25_enabled", "BOOLEAN NOT NULL DEFAULT 1" if dialect == "mysql" else "BOOLEAN NOT NULL DEFAULT TRUE"),
            ("retrieval_bm25_k1", "FLOAT NOT NULL DEFAULT 1.5"),
            ("retrieval_bm25_b", "FLOAT NOT NULL DEFAULT 0.75"),
            ("rerank_provider", "VARCHAR(20) NOT NULL DEFAULT 'lexical'"),
            ("rerank_model", "VARCHAR(100) NULL"),
            ("retrieval_query_rewrite_enabled", "BOOLEAN NOT NULL DEFAULT 0" if dialect == "mysql" else "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("retrieval_query_rewrite_count", "INTEGER NOT NULL DEFAULT 3"),
            ("chunk_semantic_threshold", "FLOAT NOT NULL DEFAULT 0.7"),
            ("chunk_parent_enabled", "BOOLEAN NOT NULL DEFAULT 1" if dialect == "mysql" else "BOOLEAN NOT NULL DEFAULT TRUE"),
            ("indexed_embedding_key", "VARCHAR(255) NULL"),
            ("reindex_status", "VARCHAR(20) NOT NULL DEFAULT 'idle'"),
        ]
        for col_name, col_def in kb_patches:
            if col_name not in cols:
                conn.execute(
                    text(f"ALTER TABLE knowledge_bases ADD COLUMN {col_name} {col_def}")
                )
                applied.append(f"knowledge_bases.{col_name}")

    # ---- user fields added for channel rental ----
    if "users" in inspect(conn).get_table_names():
        cols = _column_names(conn, "users")
        user_patches = [
            ("email", "VARCHAR(255) NULL"),
            ("account_status", "VARCHAR(20) NOT NULL DEFAULT 'active'"),
        ]
        for col_name, col_def in user_patches:
            if col_name not in cols:
                conn.execute(
                    text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                )
                applied.append(f"users.{col_name}")

    # ---- customer_configs fields for channel rental ----
    if "customer_configs" in inspect(conn).get_table_names():
        cols = _column_names(conn, "customer_configs")
        cc_patches = [
            ("plan", "VARCHAR(20) NOT NULL DEFAULT 'free'"),
            ("trial_ends_at", "DATETIME NULL"),
            ("template_id", "VARCHAR(36) NULL"),
            ("channel_category", "VARCHAR(50) NOT NULL DEFAULT 'customer_service'"),
            ("usage_messages_month", "INTEGER NOT NULL DEFAULT 0"),
            ("usage_tokens_month", "INTEGER NOT NULL DEFAULT 0"),
            ("usage_documents_count", "INTEGER NOT NULL DEFAULT 0"),
            ("usage_storage_bytes", "INTEGER NOT NULL DEFAULT 0"),
            ("usage_messages_limit", "INTEGER NOT NULL DEFAULT 1000"),
            ("usage_tokens_limit", "INTEGER NOT NULL DEFAULT 100000"),
            ("last_usage_reset_at", "DATETIME NULL"),
        ]
        for col_name, col_def in cc_patches:
            if col_name not in cols:
                conn.execute(
                    text(
                        f"ALTER TABLE customer_configs ADD COLUMN {col_name} {col_def}"
                    )
                )
                applied.append(f"customer_configs.{col_name}")
        if "template_id" in _column_names(conn, "customer_configs"):
            try:
                conn.execute(
                    text(
                        "CREATE INDEX idx_customer_configs_template_id "
                        "ON customer_configs(template_id)"
                    )
                )
            except Exception:
                pass

    # ---- messages: token tracking ----
    if "messages" in inspect(conn).get_table_names():
        cols = _column_names(conn, "messages")
        msg_patches = [
            ("prompt_tokens", "INTEGER NULL"),
            ("completion_tokens", "INTEGER NULL"),
        ]
        for col_name, col_def in msg_patches:
            if col_name not in cols:
                conn.execute(
                    text(f"ALTER TABLE messages ADD COLUMN {col_name} {col_def}")
                )
                applied.append(f"messages.{col_name}")

    # document_chunks migration
    if "document_chunks" in inspect(conn).get_table_names():
        cols = _column_names(conn, "document_chunks")
        dc_patches = [
            ("parent_content", "TEXT NULL"),
            ("chunk_type", "VARCHAR(10) NOT NULL DEFAULT 'child'"),
        ]
        for col_name, col_def in dc_patches:
            if col_name not in cols:
                conn.execute(
                    text(f"ALTER TABLE document_chunks ADD COLUMN {col_name} {col_def}")
                )
                applied.append(f"document_chunks.{col_name}")

    # Ensure any new tables from models exist
    Base.metadata.create_all(conn)
    return applied
