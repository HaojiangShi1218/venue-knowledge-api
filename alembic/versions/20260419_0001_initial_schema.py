"""Initial Phase 4 schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260419_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "query_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("normalized_question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "venues",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=False),
        sa.Column("neighborhood", sa.String(length=255), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("price_per_head_usd", sa.Integer(), nullable=True),
        sa.Column("venue_type", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amenities", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("outside_catering", sa.Boolean(), nullable=True),
        sa.Column("alcohol_allowed", sa.Boolean(), nullable=True),
        sa.Column("min_notice_days", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_venues_capacity", "venues", ["capacity"], unique=False)
    op.create_index("ix_venues_city", "venues", ["city"], unique=False)
    op.create_index("ix_venues_external_id", "venues", ["external_id"], unique=True)
    op.create_index("ix_venues_neighborhood", "venues", ["neighborhood"], unique=False)
    op.create_index("ix_venues_venue_type", "venues", ["venue_type"], unique=False)

    op.create_table(
        "source_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_doc_id", sa.String(length=255), nullable=True),
        sa.Column("venue_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("ingestion_status", sa.String(length=50), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_source_documents_external_doc_id", "source_documents", ["external_doc_id"], unique=True)
    op.create_index("ix_source_documents_venue_id", "source_documents", ["venue_id"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("venue_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("normalized_content", sa.Text(), nullable=False),
        sa.Column("document_title", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["source_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"], unique=False)
    op.create_index(
        "ix_document_chunks_document_id_chunk_index",
        "document_chunks",
        ["document_id", "chunk_index"],
        unique=False,
    )
    op.create_index("ix_document_chunks_venue_id", "document_chunks", ["venue_id"], unique=False)

    op.create_table(
        "query_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query_log_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["query_log_id"], ["query_logs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_query_sources_chunk_id", "query_sources", ["chunk_id"], unique=False)
    op.create_index("ix_query_sources_query_log_id", "query_sources", ["query_log_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_query_sources_query_log_id", table_name="query_sources")
    op.drop_index("ix_query_sources_chunk_id", table_name="query_sources")
    op.drop_table("query_sources")

    op.drop_index("ix_document_chunks_venue_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_id_chunk_index", table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_source_documents_venue_id", table_name="source_documents")
    op.drop_index("ix_source_documents_external_doc_id", table_name="source_documents")
    op.drop_table("source_documents")

    op.drop_index("ix_venues_venue_type", table_name="venues")
    op.drop_index("ix_venues_neighborhood", table_name="venues")
    op.drop_index("ix_venues_external_id", table_name="venues")
    op.drop_index("ix_venues_city", table_name="venues")
    op.drop_index("ix_venues_capacity", table_name="venues")
    op.drop_table("venues")

    op.drop_table("query_logs")
