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

    # Ensure any new tables from models exist
    Base.metadata.create_all(conn)
    return applied
