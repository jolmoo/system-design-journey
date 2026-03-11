# 03 - Async Job Processing

Evolution of project 02. After adding Redis as a cache layer, the next step was to decouple heavy work from the request-response cycle. By introducing a Redis job queue and a worker, the API can respond immediately while background tasks are processed asynchronously.

A hands-on system design project to understand how asynchronous job queues work in a distributed architecture.
Built with Docker, NGINX, Flask, Redis and PostgreSQL.

## Architecture

If one API instance receives the job creation request, another API instance can still read its status later because everything is stored centrally in PostgreSQL and Redis.

## Technologies

- **Docker & Docker Compose** - Containerization and orchestration
- **NGINX** - Load balancer with round robin
- **Flask (Python)** - REST API
- **Redis** - Cache layer + Job queue
- **PostgreSQL** - Persistent job storage
- **Worker** - Background processor for heavy tasks

## How it works

In project 02, everything happened inside the request-response cycle:
```
Client waits → API works → Client gets response
```

If the work took 5 seconds, the client stayed blocked for 5 seconds.

In project 03, the work is decoupled from the request:
```
Client gets immediate response → Worker processes in parallel
```

The client never waits for the heavy task to finish.
The work happens in another process, in another container, at another time.

### When the client sends `POST /jobs`

1. NGINX receives the request and load balances it to one of the two API instances
2. The API generates a unique `job_id`
3. The API stores the job in PostgreSQL with `status = queued`
4. The API pushes the job into the Redis queue
5. The API responds immediately with the `job_id`

### In parallel, the worker

1. Keeps listening to Redis for new jobs
2. Detects a new queued job
3. Updates PostgreSQL to `status = processing`
4. Executes the heavy work (5 seconds)
5. Updates PostgreSQL to `status = completed` with the result

### When the client sends `GET /jobs/<id>`

1. NGINX load balances the request to one of the API instances
2. The API checks PostgreSQL
3. The API returns the current job status (`queued`, `processing`, or `completed`)

## Why this matters

This architecture introduces asynchronous processing.

The API is no longer responsible for doing the heavy work during the request.
Its only responsibility is to accept the job and return quickly.

That brings several advantages:

- Faster response time for the client
- Better user experience
- Better scalability for heavy tasks
- Clear separation between request handling and background processing
- More realistic distributed system design

## Project Structure
```
03-async-job-processing/
├── docker-compose.yml
├── api/
│   ├── app.py
│   ├── tasks.py
│   ├── Dockerfile
│   └── requirements.txt
├── worker/
│   ├── worker.py
│   ├── tasks.py
│   ├── Dockerfile
│   └── requirements.txt
└── nginx/
    └── nginx.conf
```

## Getting Started

### Requirements

- Docker
- Docker Compose

### Run the project
```bash
docker-compose up --build
```

Then open your browser or API client at:
```
http://localhost
```

### Stop the project
```bash
docker-compose down
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /jobs` | Creates a new background job and returns a `job_id` immediately |
| `GET /jobs/<id>` | Returns the current status of the job |
| `GET /db` | Checks database connection |
| `GET /` | Basic API response showing instance name |

## Job Queue Tests

### Test 1 - Create a job
```bash
curl -X POST http://localhost/jobs \
  -H "Content-Type: application/json" \
  -d '{"type": "report"}'
```

You should receive something like:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued"
}
```

The response is immediate. The heavy work has not finished yet.

### Test 2 - Check job status
```bash
curl http://localhost/jobs/<job_id>
```

At first:
```json
{ "status": "queued" }
```

Then:
```json
{ "status": "processing" }
```

Finally:
```json
{
  "status": "completed",
  "result": "Report generated for job ... of type report"
}
```

### Test 3 - Confirm asynchronous behavior

Create a job and notice that the API responds immediately, even though the worker takes 5 seconds to complete it. This proves the client is no longer blocked by heavy processing.

### Test 4 - Multiple jobs
```bash
curl -X POST http://localhost/jobs -H "Content-Type: application/json" -d '{"type": "report"}'
curl -X POST http://localhost/jobs -H "Content-Type: application/json" -d '{"type": "report"}'
curl -X POST http://localhost/jobs -H "Content-Type: application/json" -d '{"type": "report"}'
```

All of them are queued quickly, and the worker processes them one by one in the background.

## What I learned

- The difference between synchronous and asynchronous processing
- Why job queues are useful in distributed systems
- How Redis can be used as a message broker / queue
- How a worker can process tasks independently from the API
- Why PostgreSQL is useful for persistent job state
- How to design systems where the client does not wait for heavy work
- How to separate concerns between load balancing, API handling, queueing and processing

## Author

Made by jolmo as part of the [system design journey](https://github.com/jolmoo/system-design-journey).
