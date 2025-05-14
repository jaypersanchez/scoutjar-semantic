import os
from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer
from datetime import datetime

# Load .env
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Load local embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS talent_profile_embeddings (
    talent_id INTEGER PRIMARY KEY,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# Fetch talents not yet embedded
cursor.execute("""
SELECT tp.talent_id, tp.bio, tp.resume, tp.skills, tp.experience, tp.location, tp.availability, up.full_name
FROM talent_profiles tp
JOIN user_profiles up ON tp.user_id = up.user_id
WHERE tp.talent_id NOT IN (SELECT talent_id FROM talent_profile_embeddings)
""")
rows = cursor.fetchall()

# Embed and store
for talent_id, bio, resume, skills, exp, loc, avail, full_name in rows:
    text = f"{full_name or ''}. {bio or ''}. {resume or ''}. Skills: {', '.join(skills or [])}. Experience: {exp or ''}. Location: {loc or ''}. Availability: {avail or ''}"
    embedding = model.encode(text).tolist()

    cursor.execute("""
        INSERT INTO talent_profile_embeddings (talent_id, embedding, created_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (talent_id) DO NOTHING;
    """, (talent_id, embedding, datetime.utcnow()))

    print(f"✅ Embedded talent_id={talent_id}")

conn.commit()
cursor.close()
conn.close()
