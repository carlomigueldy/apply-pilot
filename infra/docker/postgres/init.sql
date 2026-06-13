-- ApplyPilot Postgres bootstrap.
-- Runs once on first container start (empty data directory).
-- Enables the pgvector extension used for 1536-dim embedding columns.
CREATE EXTENSION IF NOT EXISTS vector;
