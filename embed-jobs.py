import os
from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer
from datetime import datetime

# 🔄 Load environment variables
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# 🧠 Load embedding model (384-dim)
model = SentenceTransformer('all-MiniLM-L6-v2')

# ✅ Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()

# 🔧 Create embeddings table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS job_post_embeddings (
    job_id INTEGER PRIMARY KEY,
    embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# 🔍 Fetch job posts (avoid already embedded)
def fetch_jobs():
    cursor.execute("""
        SELECT job_id, job_title, job_description, required_skills, location
        FROM jobs
        WHERE job_id NOT IN (SELECT job_id FROM job_post_embeddings)
    """)
    return cursor.fetchall()

# ⚙️ Generate embedding and insert
def embed_and_store(jobs):
    for job_id, title, desc, skills, location in jobs:
        text = f"{title or ''}. Skills: {', '.join(skills or [])}. {desc or ''} Location: {location or ''}"
        embedding = model.encode(text).tolist()

        cursor.execute("""
            INSERT INTO job_post_embeddings (job_id, embedding, created_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (job_id) DO NOTHING;
        """, (job_id, embedding, datetime.utcnow()))
        print(f"✅ Embedded job_id={job_id}")

    conn.commit()

# 🚀 Run
if __name__ == "__main__":
    print("📥 Fetching jobs to embed...")
    jobs = fetch_jobs()
    if jobs:
        print(f"🧠 Embedding {len(jobs)} job(s)...")
        embed_and_store(jobs)
    else:
        print("✅ All jobs already embedded.")

    cursor.close()
    conn.close()
