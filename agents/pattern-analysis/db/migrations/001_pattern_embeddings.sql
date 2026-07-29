-- PA-FR-005 pgvector persistence (optional)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS pattern_embeddings (
    pattern_id          TEXT NOT NULL,
    embedding           VECTOR(128) NOT NULL,
    embedding_dimension INTEGER NOT NULL DEFAULT 128,
    embedding_version   TEXT NOT NULL,
    algorithm_name      TEXT NOT NULL,
    feature_version     TEXT NOT NULL,
    source_file         TEXT,
    created_timestamp   TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (pattern_id, embedding_version)
);

CREATE INDEX IF NOT EXISTS idx_pattern_embeddings_version
    ON pattern_embeddings (embedding_version);
