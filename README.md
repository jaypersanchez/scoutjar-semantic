# PostgreSQL Setup for Semantic Talent Matching

## Run on remote server

1. Install pgvector Extension

sudo apt install postgresql-server-dev-14  # or use 15/16 depending on your PostgreSQL version
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

2. Enable pgvector in Database

CREATE EXTENSION IF NOT EXISTS vector;

3. Create Vector Table for Job Embeddings

CREATE TABLE IF NOT EXISTS job_post_embeddings (
    job_id INTEGER PRIMARY KEY REFERENCES jobs(job_id) ON DELETE CASCADE,
    embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

** 384 is for the all-MiniLM-L6-v2 model. Use 768 for BERT-base, etc. **

4. Option: Add Similarity Index (IVFFLAT) - Improves vector search performance

CREATE INDEX IF NOT EXISTS job_post_embeddings_vector_idx
ON job_post_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

** Run ANALYZE job_post_embeddings; after you’ve inserted enough rows. **

5. Add profile_mode Column to talent_profiles

ALTER TABLE talent_profiles
ADD COLUMN IF NOT EXISTS profile_mode VARCHAR(10) DEFAULT 'active';


6. Create passive_preferences Table

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

7. Create passive_matches Table

CREATE TABLE IF NOT EXISTS passive_matches (
    id SERIAL PRIMARY KEY,
    talent_id INTEGER REFERENCES talent_profiles(talent_id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
    recruiter_id INTEGER,
    match_score INTEGER,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (talent_id, job_id)
);

Analyze after inserting embeddings

** ANALYZE job_post_embeddings; **






