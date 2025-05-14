import os
from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer
from datetime import datetime

load_dotenv()

# 🔧 DB config
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# 🔍 Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Connect DB
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()

# Step 1: Get all passive preference records
cursor.execute("""
    SELECT 
        pp.talent_id,
        pp.salary_min,
        pp.salary_max,
        pp.remote_preference,
        pp.match_threshold,
        pp.dream_companies,
        pp.preferred_industries,
        pp.preferred_roles
    FROM passive_preferences pp
    JOIN talent_profiles tp ON tp.talent_id = pp.talent_id
    WHERE tp.profile_mode = 'passive';
""")

passive_records = cursor.fetchall()

# Step 2: Process each passive talent
for row in passive_records:
    talent_id, s_min, s_max, remote, threshold, companies, industries, roles = row

    # Step 3: Build search query string
    query_parts = []
    if roles: query_parts.append("Roles: " + ", ".join(roles))
    if industries: query_parts.append("Industries: " + ", ".join(industries))
    if remote: query_parts.append("Remote OK")
    query_parts.append(f"Salary: {s_min} to {s_max}")
    prompt = ". ".join(query_parts)
    print(f"\n🎯 Talent ID: {talent_id}")
    print(f"📝 Prompt: {prompt}")

    query_vector = model.encode(prompt).tolist()

    # Step 4: Find top N matches (including recruiter_id)
    cursor.execute("""
        SELECT j.job_id, j.job_title, j.recruiter_id,
               job_post_embeddings.embedding <=> %s::vector AS similarity
        FROM job_post_embeddings
        JOIN jobs j ON j.job_id = job_post_embeddings.job_id
        ORDER BY similarity ASC
        LIMIT 10;
    """, (query_vector,))
    results = cursor.fetchall()

    # Step 5: Filter by match threshold (based on distance-to-score)
    for job_id, title, recruiter_id, similarity in results:
        match_score = max(0, int((1 - similarity) * 100))
        if match_score >= threshold:
            message = f"💡 Match found: '{title}' (Score: {match_score}%)"

            # ✅ Store match in passive_matches table
            cursor.execute("""
                INSERT INTO passive_matches (talent_id, job_id, recruiter_id, match_score)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (talent_id, job_id) DO NOTHING;
            """, (talent_id, job_id, recruiter_id, match_score))

            # ✅ Clean print output
            print(f"📬 Talent {talent_id} matched Job {job_id}")
            print(f"   🔹 Title: {title}")
            print(f"   🎯 Score: {match_score}% | Recruiter: {recruiter_id}")
            print("-" * 60)

conn.commit()
cursor.close()
conn.close()
