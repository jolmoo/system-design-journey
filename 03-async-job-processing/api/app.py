import os
import psycopg2
import redis
import uuid
import time
from tasks import process_job
from flask import Flask, request, jsonify
from rq import Queue

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        dbname=os.environ.get("DB_NAME", "mydb"),
        user=os.environ.get("DB_USER", "user"),
        password=os.environ.get("DB_PASSWORD", "password")
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id VARCHAR(36) PRIMARY KEY,
            status VARCHAR(20) NOT NULL,
            result TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

app = Flask(__name__)
INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "api")
cache = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=6379
)
job_queue = Queue('jobs', connection=cache)

@app.route("/")
def home():
    try:
        cached = cache.get("home_response")
        if cached:
            return {"message": "Hello from cache", "instance": INSTANCE_NAME}
        cache.set("home_response", "true", ex=30)
    except Exception:
        pass
    return {"message": "Hello from database", "instance": INSTANCE_NAME}

@app.route("/cache-status")
def cache_status():
    try:
        cached = cache.get("home_response")
        return {
            "instance": INSTANCE_NAME,
            "cache": "hit" if cached else "miss",
            "ttl": cache.ttl("home_response")
        }
    except Exception:
        pass
    return {"message": "No Redis Available", "instance": INSTANCE_NAME}

@app.route("/db")
def check_db():
    try:
        conn = get_db_connection()
        conn.close()
        return {"instance": INSTANCE_NAME, "database": "connected"}
    except Exception as e:
        return {"instance": INSTANCE_NAME, "database": "error"}, 500

@app.route("/jobs", methods=["POST"])
def create_job():
    data = request.get_json()
    job_type = data.get("type", "report")
    job_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jobs (id, status) VALUES (%s, %s)",
        (job_id, "queued")
    )
    conn.commit()
    cursor.close()
    conn.close()
    job_queue.enqueue(process_job, job_id, job_type) 
    return jsonify({"job_id": job_id, "status": "queued"}), 201

@app.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, status, result, created_at, updated_at FROM jobs WHERE id = %s",
        (job_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row is None:
        return jsonify({"error": "job not found"}), 404
    return jsonify({
        "job_id": row[0],
        "status": row[1],
        "result": row[2],
        "created_at": str(row[3]),
        "updated_at": str(row[4])
    })

def init_db_with_retry():
    retries = 5
    while retries > 0:
        try:
            init_db()
            print("Database initialized")
            return
        except Exception as e:
            print(f"DB not ready, retrying... ({e})")
            retries -= 1
            time.sleep(3)

with app.app_context():
    init_db_with_retry()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)