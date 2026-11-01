"""Merge the RAG pricing and study-file checksum migration branches."""

revision = "20261101_0034"
down_revision = ("20261101_0032", "20261029_0033")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Schema changes are contained in the two parent revisions.
    pass


def downgrade() -> None:
    # Keep the merged database revision intact; the parent migrations own DDL.
    pass
