import os
import sys
from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer

load_dotenv()

# ✅ Parse search text from CLI
if len(sys.argv) < 2:
    print("❗Usage: python3 search-jobs.py \"your search query here\"")
    sys.exit(1)

query_text = sys.argv[1]

# 🔑 DB credentials
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# 🔍 Load model
model = SentenceTransformer('all-MiniLM-L6-v2')
query_vector = model.encode(query_text).tolist()

# 🧠 Connect to DB
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()

# 🔎 Query top matches
cursor.execute("""
    SELECT j.job_id, j.job_title, j.job_description, j.location,
           job_post_embeddings.embedding <=> %s::vector AS similarity
    FROM job_post_embeddings
    JOIN jobs j ON j.job_id = job_post_embeddings.job_id
    ORDER BY similarity ASC
    LIMIT 5;
""", (query_vector,))

results = cursor.fetchall()
cursor.close()
conn.close()

# 📊 Output
print(f"\n🔍 Results for: \"{query_text}\"")
for job_id, title, desc, loc, sim in results:
    # Determine match quality
    match_quality = (
        "🟢 Strong match" if sim < 0.4 else
        "🟡 Moderate match" if sim < 0.6 else
        "🔴 Weak match"
    )

    print(f"\n🆔 Job ID: {job_id}")
    print(f"📌 Title: {title or 'N/A'}")
    print(f"📍 Location: {loc or 'N/A'}")
    print(f"📉 Distance: {sim:.4f} ({match_quality})")
    print(f"📝 Description: {(desc or '')[:180]}...")

    # Optional content completeness warning
    if not any([title, desc]):
        print("⚠️ This job post is missing key details. Encourage the recruiter to complete the post for better matching.")
