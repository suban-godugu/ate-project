"""Alembic revision: FA-FR-001 production ingestion schema (idempotent).

Revision ID: 002_fa_fr_001_ingestion
Revises: 001_initial_schema

Safe when tables were already bootstrapped via SQLAlchemy ``create_all``.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "002_fa_fr_001_ingestion"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in {c["name"] for c in inspect(bind).get_columns(table)}


def _has_index(table: str, index: str) -> bool:
    bind = op.get_bind()
    return index in {i["name"] for i in inspect(bind).get_indexes(table)}


def _ensure_index(table: str, index: str, columns: list[str]) -> None:
    if not _has_index(table, index):
        op.create_index(index, table, columns)


def upgrade() -> None:
    if _has_table("uploads"):
        if _has_column("uploads", "file_size_bytes"):
            op.execute(
                "ALTER TABLE uploads ALTER COLUMN file_size_bytes TYPE BIGINT "
                "USING file_size_bytes::bigint"
            )
        for col, ddl in [
            ("dataset_id", "ALTER TABLE uploads ADD COLUMN dataset_id VARCHAR(36)"),
            ("sanitized_filename", "ALTER TABLE uploads ADD COLUMN sanitized_filename VARCHAR(512)"),
            ("relative_path", "ALTER TABLE uploads ADD COLUMN relative_path VARCHAR(1024)"),
            ("detected_mime", "ALTER TABLE uploads ADD COLUMN detected_mime VARCHAR(128)"),
            ("created_by", "ALTER TABLE uploads ADD COLUMN created_by VARCHAR(128)"),
            ("tenant_id", "ALTER TABLE uploads ADD COLUMN tenant_id VARCHAR(128)"),
        ]:
            if not _has_column("uploads", col):
                op.execute(ddl)
        _ensure_index("uploads", "ix_uploads_dataset_id", ["dataset_id"])
        _ensure_index("uploads", "ix_uploads_tenant_id", ["tenant_id"])

    if not _has_table("ingestion_datasets"):
        op.create_table(
            "ingestion_datasets",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("name", sa.String(length=512), nullable=False),
            sa.Column("source_root", sa.String(length=1024), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("stil_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("log_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("records_accepted", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("records_quarantined", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_by", sa.String(length=128), nullable=True),
            sa.Column("tenant_id", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
    _ensure_index("ingestion_datasets", "ix_ingestion_datasets_name", ["name"])
    _ensure_index("ingestion_datasets", "ix_ingestion_datasets_status", ["status"])
    _ensure_index("ingestion_datasets", "ix_ingestion_datasets_tenant_id", ["tenant_id"])

    if not _has_table("upload_history"):
        op.create_table(
            "upload_history",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("upload_id", sa.String(length=36), sa.ForeignKey("uploads.id", ondelete="CASCADE")),
            sa.Column("from_status", sa.String(length=32), nullable=True),
            sa.Column("to_status", sa.String(length=32), nullable=False),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("actor", sa.String(length=128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    _ensure_index("upload_history", "ix_upload_history_upload_id", ["upload_id"])

    if not _has_table("parser_metadata"):
        op.create_table(
            "parser_metadata",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("upload_id", sa.String(length=36), sa.ForeignKey("uploads.id", ondelete="CASCADE")),
            sa.Column("parser_id", sa.String(length=64), nullable=False),
            sa.Column("parser_version", sa.String(length=32), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    _ensure_index("parser_metadata", "ix_parser_metadata_upload_id", ["upload_id"])
    _ensure_index("parser_metadata", "ix_parser_metadata_parser_id", ["parser_id"])

    if not _has_table("validation_results"):
        op.create_table(
            "validation_results",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("upload_id", sa.String(length=36), sa.ForeignKey("uploads.id", ondelete="CASCADE")),
            sa.Column(
                "dataset_id",
                sa.String(length=36),
                sa.ForeignKey("ingestion_datasets.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("severity", sa.String(length=16), nullable=False),
            sa.Column("category", sa.String(length=64), nullable=False),
            sa.Column("code", sa.String(length=64), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    _ensure_index("validation_results", "ix_validation_results_upload_id", ["upload_id"])
    _ensure_index("validation_results", "ix_validation_results_dataset_id", ["dataset_id"])
    _ensure_index("validation_results", "ix_validation_results_severity", ["severity"])

    if not _has_table("normalized_records"):
        op.create_table(
            "normalized_records",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("upload_id", sa.String(length=36), sa.ForeignKey("uploads.id", ondelete="CASCADE")),
            sa.Column(
                "dataset_id",
                sa.String(length=36),
                sa.ForeignKey("ingestion_datasets.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("record_key", sa.String(length=512), nullable=False),
            sa.Column("lot_id", sa.String(length=128), nullable=False),
            sa.Column("wafer_id", sa.String(length=128), nullable=False),
            sa.Column("die_id", sa.String(length=128), nullable=False),
            sa.Column("test_stage", sa.String(length=64), nullable=False),
            sa.Column("tester_id", sa.String(length=128), nullable=False),
            sa.Column("pass_fail", sa.String(length=16), nullable=False),
            sa.Column("timestamp", sa.String(length=64), nullable=False),
            sa.Column("adapter_id", sa.String(length=64), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("upload_id", "record_key", name="uq_normalized_upload_record_key"),
        )
    _ensure_index("normalized_records", "ix_normalized_records_upload_id", ["upload_id"])
    _ensure_index("normalized_records", "ix_normalized_records_dataset_id", ["dataset_id"])
    _ensure_index("normalized_records", "ix_normalized_records_lot_id", ["lot_id"])
    _ensure_index("normalized_records", "ix_normalized_records_wafer_id", ["wafer_id"])
    _ensure_index("normalized_records", "ix_normalized_records_die_id", ["die_id"])
    _ensure_index("normalized_records", "ix_normalized_records_pass_fail", ["pass_fail"])

    if not _has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.String(length=36), nullable=False),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("actor", sa.String(length=128), nullable=True),
            sa.Column("tenant_id", sa.String(length=128), nullable=True),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    _ensure_index("audit_logs", "ix_audit_logs_entity_type", ["entity_type"])
    _ensure_index("audit_logs", "ix_audit_logs_entity_id", ["entity_id"])
    _ensure_index("audit_logs", "ix_audit_logs_action", ["action"])
    _ensure_index("audit_logs", "ix_audit_logs_tenant_id", ["tenant_id"])
    _ensure_index("audit_logs", "ix_audit_logs_created_at", ["created_at"])

    if not _has_table("ingestion_statistics"):
        op.create_table(
            "ingestion_statistics",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column(
                "upload_id",
                sa.String(length=36),
                sa.ForeignKey("uploads.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column(
                "dataset_id",
                sa.String(length=36),
                sa.ForeignKey("ingestion_datasets.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("upload_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("validation_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("parse_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("normalize_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("persist_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("total_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("records_parsed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("records_accepted", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("records_quarantined", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("records_per_minute", sa.Float(), nullable=False, server_default="0"),
            sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("parser_id", sa.String(length=64), nullable=True),
            sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    _ensure_index("ingestion_statistics", "ix_ingestion_statistics_upload_id", ["upload_id"])
    _ensure_index("ingestion_statistics", "ix_ingestion_statistics_dataset_id", ["dataset_id"])


def downgrade() -> None:
    for table in (
        "ingestion_statistics",
        "audit_logs",
        "normalized_records",
        "validation_results",
        "parser_metadata",
        "upload_history",
        "ingestion_datasets",
    ):
        if _has_table(table):
            op.drop_table(table)
    if _has_table("uploads"):
        for index in ("ix_uploads_tenant_id", "ix_uploads_dataset_id"):
            if _has_index("uploads", index):
                op.drop_index(index, table_name="uploads")
        for col in (
            "tenant_id",
            "created_by",
            "detected_mime",
            "relative_path",
            "sanitized_filename",
            "dataset_id",
        ):
            if _has_column("uploads", col):
                op.drop_column("uploads", col)
        op.execute(
            "ALTER TABLE uploads ALTER COLUMN file_size_bytes TYPE INTEGER "
            "USING LEAST(file_size_bytes, 2147483647)::integer"
        )
