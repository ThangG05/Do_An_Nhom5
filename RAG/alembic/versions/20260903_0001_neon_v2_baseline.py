"""HVNH Hub and AI/RAG schema V2 baseline.

Revision ID: 20260903_0001
Revises: None
"""
from collections.abc import Sequence
from pathlib import Path

from alembic import op

revision: str = "20260903_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _schema_sql() -> str:
    path = Path(__file__).resolve().parents[2] / "base_v2.sql"
    if not path.is_file():
        raise RuntimeError(f"Schema specification not found: {path}")
    sql = path.read_text(encoding="utf-8")
    return "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))


def upgrade() -> None:
    # This revision is for a clean database. For an existing Neon database created
    # from base_v2.sql, use: alembic stamp 20260903_0001
    connection = op.get_bind()
    for statement in _schema_sql().split(";"):
        statement = statement.strip()
        if statement:
            connection.exec_driver_sql(statement)


def downgrade() -> None:
    # Extensions are deliberately retained because other schemas may use them.
    connection = op.get_bind()
    tables = [
        "audit_logs", "ai_message_citations", "ai_messages", "ai_conversations",
        "ai_document_chunks", "ai_document_versions", "ai_documents", "notifications",
        "message_receipts", "message_attachments", "messages", "conversation_members",
        "conversations", "user_blocks", "friendships", "friend_requests", "reports",
        "post_likes", "comments", "post_media", "media_files", "posts", "group_members",
        "groups", "refresh_tokens", "email_verification_codes", "user_roles", "roles",
        "profiles", "users",
    ]
    for table in tables:
        connection.exec_driver_sql(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    enum_types = [
        "ai_message_role", "ai_visibility", "ai_document_status", "ai_document_type",
        "report_target_type", "report_status", "notification_type", "message_type",
        "conversation_type", "friend_request_status", "post_status", "group_status",
        "group_role", "account_status",
    ]
    for enum_type in enum_types:
        connection.exec_driver_sql(f'DROP TYPE IF EXISTS "{enum_type}"')
