import os
import psycopg2
import redis
from flask import Flask

app = Flask(__name__)
INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "api")
cache = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=6379
)

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
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "db"),
            dbname=os.environ.get("DB_NAME", "mydb"),
            user=os.environ.get("DB_USER", "user"),
            password=os.environ.get("DB_PASSWORD", "password")
        )
        conn.close()
        return {"instance": INSTANCE_NAME, "database": "connected"}
    except Exception as e:
        return {"instance": INSTANCE_NAME, "database": "error"}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
