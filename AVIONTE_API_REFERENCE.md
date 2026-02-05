# Avionté API Reference

## Internal API Endpoints

This document describes the internal API endpoints for Avionté integration.

### Health Check

**GET** `/api/avionte/health`

Check Avionté API health and configuration status.

**Response:**
```json
{
  "status": "healthy",
  "avionte_configured": true
}
```

### Sync Candidate to Avionté

**POST** `/api/avionte/sync/candidate/{candidate_id}`

Sync a candidate to Avionté.

**Query Parameters:**
- `force_update` (boolean, optional): Force update even if already synced

**Response:**
```json
{
  "success": true,
  "candidate_id": "uuid",
  "avionte_talent_id": "avionte-id",
  "action": "created"
}
```

### Sync Job to Avionté

**POST** `/api/avionte/sync/job/{job_id}`

Sync a job to Avionté.

**Query Parameters:**
- `force_update` (boolean, optional): Force update even if already synced

**Response:**
```json
{
  "success": true,
  "job_id": "uuid",
  "avionte_job_id": "avionte-id",
  "action": "created"
}
```

### Get Talent from Avionté

**GET** `/api/avionte/talent/{talent_id}`

Get a talent from Avionté.

**Response:**
```json
{
  "talentId": "avionte-id",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com",
  ...
}
```

### Sync Talent from Avionté

**POST** `/api/avionte/sync/from-avionte/talent/{talent_id}`

Sync a talent from Avionté to internal system.

**Response:**
```json
{
  "success": true,
  "talent_id": "avionte-id",
  "candidate_id": "internal-uuid",
  "action": "created"
}
```

### Batch Sync

**POST** `/api/avionte/sync/batch`

Batch sync candidates or jobs.

**Request Body:**
```json
{
  "sync_type": "candidates",
  "candidate_ids": ["id1", "id2"],
  "job_ids": null,
  "force_update": false
}
```

**Response:**
```json
{
  "success": true,
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "results": [...],
  "errors": []
}
```

## Avionté API Client

### Initialization

```python
from backend.services.avionte import AvionteClient

client = AvionteClient()
```

### Talent API

```python
from backend.services.avionte.talent import AvionteTalentAPI

talent_api = AvionteTalentAPI(client)

# Create talent
talent = await talent_api.create_talent(talent_model)

# Get talent
talent = await talent_api.get_talent(talent_id)

# Update talent
talent = await talent_api.update_talent(talent_id, talent_model)

# Query talents
results = await talent_api.query_talents(filters={}, page=1, page_size=50)
```

### Jobs API

```python
from backend.services.avionte.jobs import AvionteJobsAPI

jobs_api = AvionteJobsAPI(client)

# Create job
job = await jobs_api.create_job(job_model)

# Get job
job = await jobs_api.get_job(job_id)

# Update job
job = await jobs_api.update_job(job_id, job_model)

# Query jobs
results = await jobs_api.query_jobs(filters={}, page=1, page_size=50)
```

## Error Codes

- `401`: Authentication failed
- `404`: Resource not found
- `429`: Rate limit exceeded
- `500`: Internal server error
- `502`: Avionté API error

## Rate Limiting

The client automatically handles rate limiting with exponential backoff. Default retry configuration:
- Max retries: 3
- Initial delay: 1 second
- Exponential backoff: 2x per retry
