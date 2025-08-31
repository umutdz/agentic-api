# API Usage Guide for Agentic API

This guide provides comprehensive examples of how to use the Agentic API endpoints using curl commands. The API supports both code generation and content research tasks through intelligent agent routing.

## Authentication Endpoints

### Register a New User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password",
    "full_name": "John Doe"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'
```
Response will include access token and refresh token.

### Get Current User Info
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer your_access_token"
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh-token \
  -H "Authorization: Bearer your_refresh_token"
```

### Change Password
```bash
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "old_password",
    "new_password": "new_password"
  }'
```

## Agent Task Execution

### Execute a Task
Submit a task for processing. The system will automatically determine whether to use CodeAgent or ContentAgent.

```bash
curl -X POST http://localhost:8000/api/v1/agent/execute \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique_key_123" \
  -d '{
    "task": "Create a Python function to calculate fibonacci numbers with memoization"
  }'
```

**Response:**
```json
{
  "job_id": "job_abc123",
  "status": "queued",
  "message": "Task submitted successfully"
}
```

### Code Generation Task Example
```bash
curl -X POST http://localhost:8000/api/v1/agent/execute \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: code_task_456" \
  -d '{
    "task": "Write a JavaScript function to validate email addresses using regex"
  }'
```

### Content Research Task Example
```bash
curl -X POST http://localhost:8000/api/v1/agent/execute \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: research_task_789" \
  -d '{
    "task": "Research the latest developments in quantum computing and provide a summary with sources"
  }'
```

## Job Management

### Get Job Status
Check the current status and progress of a submitted task.

```bash
curl -X GET http://localhost:8000/api/v1/agent/jobs/{job_id} \
  -H "Authorization: Bearer your_access_token"
```

**Response:**
```json
{
  "job_id": "job_abc123",
  "status": "running",
  "progress": 0.6,
  "decided_agent": "code",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:32:00Z"
}
```

### Get Job Result
Once completed, retrieve the final result.

```bash
curl -X GET http://localhost:8000/api/v1/agent/jobs/{job_id} \
  -H "Authorization: Bearer your_access_token"
```

**Code Generation Result:**
```json
{
  "job_id": "job_abc123",
  "status": "succeeded",
  "progress": 1.0,
  "decided_agent": "code",
  "result": {
    "language": "python",
    "code": "def fibonacci(n, memo={}):\n    if n in memo:\n        return memo[n]\n    if n <= 1:\n        return n\n    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)\n    return memo[n]",
    "explanation": "This function implements memoization to avoid recalculating fibonacci numbers..."
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

**Content Research Result:**
```json
{
  "job_id": "job_abc123",
  "status": "succeeded",
  "progress": 1.0,
  "decided_agent": "content",
  "result": {
    "answer": "Quantum computing has seen significant advances in 2024...",
    "sources": [
      {
        "title": "Recent Advances in Quantum Computing",
        "url": "https://example.com/quantum-advances",
        "domain": "example.com"
      },
      {
        "title": "Quantum Computing Breakthroughs",
        "url": "https://research.org/quantum-breakthroughs",
        "domain": "research.org"
      }
    ]
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:38:00Z"
}
```
## Health Check

### API Health Status
```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "mongodb": "connected",
    "postgres": "connected",
    "redis": "connected",
    "rabbitmq": "connected"
  }
}
```

## Best Practices

### Idempotency
- Always include a unique `Idempotency-Key` header to prevent duplicate task execution
- Use descriptive keys that help identify the task (e.g., `user_123_fibonacci_task`)

### Task Descriptions
- **Code Generation**: Be specific about language, requirements, and context
- **Content Research**: Provide clear research questions and scope

### Polling Strategy
- Start with short intervals (1-2 seconds) for quick tasks
- Increase intervals for longer-running tasks (5-10 seconds)
- Use exponential backoff for failed requests

### Error Handling
- Check the `retryable` field in error responses
- Implement appropriate retry logic for retryable errors
- Log non-retryable errors for investigation

## Testing Scripts

For quick testing and demonstration of the API endpoints, you can use the following bash scripts. Make sure to replace `PASTE_YOUR_JWT` with your actual JWT token.

### Quick Test Script for Content Agent

```bash
#!/bin/bash

# Set your JWT token here
TOKEN='PASTE_YOUR_JWT'

echo "=== Testing ContentAgent (Content Research) ==="

# Create new job for ContentAgent, assign job_id to variable
JOB_C=$(curl -s http://localhost:8000/api/v1/agent/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 00000000-0000-0000-0000-0000000000c1" \
  -d '{"task": "Research the latest developments in quantum computing and provide a summary with sources", "mode": "async"}' \
  | python3 -c 'import sys, json; print(json.load(sys.stdin)["job_id"])')

echo "ContentAgent Job ID: $JOB_C"

# Query job status
echo "ContentAgent Job Status:"
curl -s http://localhost:8000/api/v1/agent/jobs/$JOB_C \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Quick Test Script for Code Agent
```bash
echo -e "\n=== Testing CodeAgent (Code Generation) ==="

# Create new job for CodeAgent, assign job_id to variable
JOB_ID=$(curl -s http://localhost:8000/api/v1/agent/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 00000000-0000-0000-0000-0000000000k6" \
  -d '{"task": "Create a Python function to calculate fibonacci numbers with memoization", "mode": "async"}' \
  | python3 -c 'import sys, json; print(json.load(sys.stdin)["job_id"])')

echo "CodeAgent Job ID: $JOB_ID"

# Query job status
echo "CodeAgent Job Status:"
curl -s http://localhost:8000/api/v1/agent/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n=== Testing Complete ==="
```

### Usage Instructions

1. **Set your JWT token**: Replace `PASTE_YOUR_JWT` with your actual JWT token
2. **Make script executable**: `chmod +x test_api.sh`
3. **Run the script**: `./test_api.sh`

### What the Script Does

- **ContentAgent Test**: Creates a content research job for quantum computing
- **CodeAgent Test**: Creates a code generation job for fibonacci function
- **Job ID Extraction**: Automatically extracts job IDs from responses
- **Status Querying**: Queries the status of both created jobs
- **Formatted Output**: Uses `python3 -m json.tool` for readable JSON output

### Expected Output

The script will show:
- Job IDs for both created jobs
- Current status and progress of each job
- Formatted JSON responses for easy reading

## Notes
- Replace `your_access_token` and `your_refresh_token` with actual tokens received from login/refresh endpoints
- Replace `{job_id}` with actual job ID from the execute endpoint response
- All endpoints require authentication except health check
- The `Idempotency-Key` header is required for task execution to prevent duplicates
- Job status updates are real-time and can be polled for progress monitoring
- Results are stored permanently and can be retrieved multiple times
