"""One-shot repair: create scan-chain pipeline tables if missing, stamp alembic."""
from __future__ import annotations

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

SQL = r"""
DO $$ BEGIN
  CREATE TYPE parser_job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'skipped_duplicate');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS parser_jobs (
  id UUID PRIMARY KEY,
  upload_job_id UUID NOT NULL REFERENCES upload_jobs(id) ON DELETE CASCADE,
  status parser_job_status NOT NULL DEFAULT 'pending',
  parser_id VARCHAR(64),
  confidence FLOAT,
  vendor VARCHAR(64),
  sha256 VARCHAR(64),
  duplicate_of UUID REFERENCES parser_jobs(id),
  error_message TEXT,
  unified_dataset_key VARCHAR(1024),
  failed_stage VARCHAR(64),
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_parser_jobs_upload_job_id ON parser_jobs (upload_job_id);
CREATE INDEX IF NOT EXISTS ix_parser_jobs_sha256 ON parser_jobs (sha256);

CREATE TABLE IF NOT EXISTS parser_statistics (
  id UUID PRIMARY KEY,
  parser_job_id UUID NOT NULL UNIQUE REFERENCES parser_jobs(id) ON DELETE CASCADE,
  parse_time_ms FLOAT,
  record_count INTEGER DEFAULT 0,
  quarantine_count INTEGER DEFAULT 0,
  throughput_records_per_s FLOAT,
  cache_hit BOOLEAN DEFAULT false,
  error_count INTEGER DEFAULT 0,
  extras JSONB
);

CREATE TABLE IF NOT EXISTS parsed_files (
  id UUID PRIMARY KEY,
  parser_job_id UUID NOT NULL REFERENCES parser_jobs(id) ON DELETE CASCADE,
  upload_job_id UUID NOT NULL REFERENCES upload_jobs(id) ON DELETE CASCADE,
  file_name VARCHAR(512) NOT NULL,
  file_type VARCHAR(32),
  size_bytes BIGINT DEFAULT 0,
  sha256 VARCHAR(64),
  parser_id VARCHAR(64),
  minio_bucket VARCHAR(128),
  minio_object_key VARCHAR(1024),
  status VARCHAR(32) DEFAULT 'pending',
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_parsed_files_parser_job_id ON parsed_files (parser_job_id);
CREATE INDEX IF NOT EXISTS ix_parsed_files_upload_job_id ON parsed_files (upload_job_id);

CREATE TABLE IF NOT EXISTS normalized_records (
  id UUID PRIMARY KEY,
  upload_job_id UUID NOT NULL REFERENCES upload_jobs(id) ON DELETE CASCADE,
  parser_job_id UUID REFERENCES parser_jobs(id) ON DELETE SET NULL,
  parsed_file_id UUID REFERENCES parsed_files(id) ON DELETE SET NULL,
  lot_id VARCHAR(128),
  wafer_id VARCHAR(128),
  die_id VARCHAR(128),
  pass_fail VARCHAR(16),
  scan_chain VARCHAR(128),
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_normalized_records_upload_job_id ON normalized_records (upload_job_id);
CREATE INDEX IF NOT EXISTS ix_normalized_records_lot_id ON normalized_records (lot_id);
CREATE INDEX IF NOT EXISTS ix_normalized_records_wafer_id ON normalized_records (wafer_id);
CREATE INDEX IF NOT EXISTS ix_normalized_records_die_id ON normalized_records (die_id);
CREATE INDEX IF NOT EXISTS ix_normalized_records_pass_fail ON normalized_records (pass_fail);
CREATE INDEX IF NOT EXISTS ix_normalized_records_scan_chain ON normalized_records (scan_chain);

CREATE TABLE IF NOT EXISTS pattern_results (
  id UUID PRIMARY KEY,
  upload_job_id UUID NOT NULL UNIQUE REFERENCES upload_jobs(id) ON DELETE CASCADE,
  agent_job_id VARCHAR(128),
  status VARCHAR(32) DEFAULT 'pending',
  report JSONB,
  kpis JSONB,
  artifact_key VARCHAR(1024),
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS failure_results (
  id UUID PRIMARY KEY,
  upload_job_id UUID NOT NULL UNIQUE REFERENCES upload_jobs(id) ON DELETE CASCADE,
  agent_job_id VARCHAR(128),
  status VARCHAR(32) DEFAULT 'pending',
  report JSONB,
  yield_report JSONB,
  kpis JSONB,
  artifact_key VARCHAR(1024),
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS diagnosis_results (
  id UUID PRIMARY KEY,
  upload_job_id UUID NOT NULL UNIQUE REFERENCES upload_jobs(id) ON DELETE CASCADE,
  agent_job_id VARCHAR(128),
  status VARCHAR(32) DEFAULT 'pending',
  report JSONB,
  kpis JSONB,
  recommendations JSONB,
  confidence FLOAT,
  artifact_key VARCHAR(1024),
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS recommendation_results (
  id UUID PRIMARY KEY,
  upload_job_id UUID NOT NULL UNIQUE REFERENCES upload_jobs(id) ON DELETE CASCADE,
  status VARCHAR(32) DEFAULT 'pending',
  payload JSONB,
  kpis JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dashboard_metrics (
  id UUID PRIMARY KEY,
  upload_job_id UUID NOT NULL UNIQUE REFERENCES upload_jobs(id) ON DELETE CASCADE,
  executive_kpis JSONB,
  pattern_kpis JSONB,
  failure_kpis JSONB,
  diagnosis_kpis JSONB,
  recommendation_kpis JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_execution_logs (
  id UUID PRIMARY KEY,
  upload_job_id UUID NOT NULL REFERENCES upload_jobs(id) ON DELETE CASCADE,
  stage VARCHAR(64) NOT NULL,
  agent VARCHAR(64),
  attempt INTEGER DEFAULT 1,
  status VARCHAR(32) NOT NULL,
  latency_ms FLOAT,
  error_message TEXT,
  extras JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_agent_execution_logs_upload_job_id ON agent_execution_logs (upload_job_id);
CREATE INDEX IF NOT EXISTS ix_agent_execution_logs_stage ON agent_execution_logs (stage);
"""


async def main() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.begin() as conn:
        await conn.execute(text(SQL))
        await conn.execute(text("UPDATE alembic_version SET version_num='004_scan_chain_pipeline'"))
        rows = await conn.execute(
            text(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema='public' AND table_name IN
                ('parser_jobs','parsed_files','normalized_records','pattern_results','failure_results','diagnosis_results')
                ORDER BY 1
                """
            )
        )
        print("tables:", [r[0] for r in rows])
        ver = await conn.execute(text("SELECT version_num FROM alembic_version"))
        print("alembic:", ver.scalar())
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
