import os
import sys
from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer

load_dotenv()

if len(sys.argv) < 2:
    print("❗Usage: python3 search-talents.py \"your query about desired talent\"")
    sys.exit(1)

query_text = sys.argv[1]

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

model = SentenceTransformer('all-MiniLM-L6-v2')
query_vector = model.encode(query_text).tolist()

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()

# ✅ Create embeddings table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS talent_profile_embeddings (
    talent_id INTEGER PRIMARY KEY,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# 🔎 Search top 5 matching talent profiles
cursor.execute("""
    SELECT tp.talent_id, up.full_name, tp.location, tp.availability, tp.skills,
           tp.resume, tp.bio, tp.experience,
           talent_profile_embeddings.embedding <=> %s::vector AS similarity
    FROM talent_profile_embeddings
    JOIN talent_profiles tp ON tp.talent_id = talent_profile_embeddings.talent_id
    JOIN user_profiles up ON tp.user_id = up.user_id
    ORDER BY similarity ASC
    LIMIT 5;
""", (query_vector,))

results = cursor.fetchall()
cursor.close()
conn.close()

# 📊 Output
print(f"\n🔍 Results for: \"{query_text}\"")
for tid, name, loc, avail, skills, resume, bio, exp, sim in results:
    # Compute match quality explanation
    match_quality = (
        "🟢 Strong match" if sim < 0.4 else
        "🟡 Moderate match" if sim < 0.6 else
        "🔴 Weak match"
    )

    print(f"\n🆔 Talent ID: {tid}\n👤 Name: {name}\n📍 Location: {loc or 'N/A'}\n⏰ Availability: {avail or 'N/A'}")
    print(f"🧠 Skills: {', '.join(skills or [])}\n📉 Distance: {sim:.4f} ({match_quality})")
    print(f"📝 Bio: {(bio or '')[:100]}...\n📚 Experience: {(exp or '')[:100]}...")

    # Optional user feedback
    if not any([bio, exp, skills]):
        print("⚠️ This talent profile appears incomplete. Consider improving profile data for better matching.")

