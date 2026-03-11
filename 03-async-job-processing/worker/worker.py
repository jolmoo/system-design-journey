import os
import redis
from rq import Worker, Queue

redis_conn = redis.Redis(
    host=os.environ.get("REDIS_HOST","redis"),
    port=6379
)

queue = Queue("jobs", connection=redis_conn)
worker = Worker([queue], connection=redis_conn)
worker.work()
