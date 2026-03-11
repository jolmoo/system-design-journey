import os
import time
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        dbname=os.environ.get("DB_NAME", "mydb"),
        user=os.environ.get("DB_USER", "user"),
        password=os.environ.get("DB_PASSWORD", "password")
    )

def process_job(job_id, job_type):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE jobs SET status = %s, updated_at = NOW() WHERE id = %s",
        ("processing", job_id)
    )
    conn.commit()

    time.sleep(5)

    result = f"Report generated for job {job_id} of type {job_type}"

    cursor.execute(
        "UPDATE jobs SET status = %s, result = %s, updated_at = NOW() WHERE id = %s",
        ("completed", result, job_id)
    )
    conn.commit()

    cursor.close()
    conn.close()