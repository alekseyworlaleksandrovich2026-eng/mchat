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
        if "widget_session_ttl_hours" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE customer_configs "
                    "ADD COLUMN widget_session_ttl_hours INTEGER NOT NULL DEFAULT 24"
                )
            )
            applied.append("customer_configs.widget_session_ttl_hours")

    # Ensure any new tables from models exist
    Base.metadata.create_all(conn)
    return applied
