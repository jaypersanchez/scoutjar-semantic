-- setup-vector-schema.sql
-- Generated on 2025-05-14 01:45:23

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- JOB POST EMBEDDINGS
-- ============================================
CREATE TABLE IF NOT EXISTS job_post_embeddings (
    job_id INTEGER PRIMARY KEY REFERENCES jobs(job_id) ON DELETE CASCADE,
    embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optional performance index for ANN searches
CREATE INDEX IF NOT EXISTS job_post_embeddings_vector_idx
ON job_post_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================
-- TALENT PROFILES - Add profile_mode if missing
-- ============================================
ALTER TABLE talent_profiles
ADD COLUMN IF NOT EXISTS profile_mode VARCHAR(10) DEFAULT 'active';

-- ============================================
-- PASSIVE PREFERENCES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS passive_preferences (
    talent_id INTEGER PRIMARY KEY REFERENCES talent_profiles(talent_id) ON DELETE CASCADE,
    salary_min NUMERIC,
    salary_max NUMERIC,
    dream_companies TEXT[],
    match_threshold INTEGER DEFAULT 80,
    remote_preference BOOLEAN DEFAULT TRUE,
    preferred_industries TEXT[],
    preferred_roles TEXT[],
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- ============================================
-- PASSIVE MATCHES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS passive_matches (
    id SERIAL PRIMARY KEY,
    talent_id INTEGER REFERENCES talent_profiles(talent_id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
    recruiter_id INTEGER,
    match_score INTEGER,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (talent_id, job_id)
);

-- Index to support efficient lookup by talent
CREATE INDEX IF NOT EXISTS idx_passive_matches_talent_id
ON passive_matches(talent_id);
