"""Snapshot estimated LLM token costs for RAG usage.

Revision ID: 20261101_0032
Revises: 20261020_0031
"""
from alembic import op
import sqlalchemy as sa

revision = "20261101_0032"
down_revision = "20261020_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rag_token_usage", sa.Column("cached_input_tokens", sa.Integer()))
    op.add_column("rag_token_usage", sa.Column("estimated_cost_usd", sa.Numeric(18, 10)))
    op.add_column("rag_token_usage", sa.Column("pricing_status", sa.String(40)))
    # Historical Gemini rows use the paid Standard list price as an estimate.
    # It is not an invoice amount; AI Studio Free-tier usage may have cost $0.
    op.execute("""
        UPDATE rag_token_usage
        SET estimated_cost_usd =
            (COALESCE(input_tokens, 0)::numeric * 0.30
             + COALESCE(output_tokens, 0)::numeric * 2.50) / 1000000,
            pricing_status = 'PAID_STANDARD_ESTIMATE'
        WHERE lower(provider) = 'gemini'
          AND lower(model) LIKE 'gemini-3.5-flash-lite%'
          AND input_tokens IS NOT NULL AND output_tokens IS NOT NULL
    """)
    op.execute("""
        UPDATE rag_token_usage SET pricing_status = 'UNPRICED'
        WHERE pricing_status IS NULL
    """)


def downgrade() -> None:
    op.drop_column("rag_token_usage", "pricing_status")
    op.drop_column("rag_token_usage", "estimated_cost_usd")
    op.drop_column("rag_token_usage", "cached_input_tokens")
