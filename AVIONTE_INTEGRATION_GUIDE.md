# Avionté Integration Guide

## Overview

This guide explains how to set up and use the Avionté API integration in the ResponsAble candidate ranking application. The integration allows you to sync candidates and jobs between the internal system and Avionté.

## Prerequisites

1. Avionté API credentials (Client ID and Client Secret)
2. Access to Avionté API documentation
3. Network access to `https://api.avionte.com`

## Setup Instructions

### 1. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Avionté API Configuration
AVIONTE_CLIENT_ID=your-avionte-client-id
AVIONTE_CLIENT_SECRET=your-avionte-client-secret
AVIONTE_API_BASE_URL=https://api.avionte.com
AVIONTE_TENANT_ID=your-tenant-id
AVIONTE_SYNC_ENABLED=false
AVIONTE_SYNC_INTERVAL=60
```

### 2. Install Dependencies

The integration requires `httpx` for async HTTP requests:

```bash
pip install -r requirements.txt
```

### 3. Verify Configuration

Check if Avionté is configured:

```python
from config import AvionteConfig

if AvionteConfig.is_configured():
    print("Avionté is configured")
else:
    print("Avionté is not configured")
```

### 4. Test API Connection

Use the health check endpoint:

```bash
curl http://localhost:8000/api/avionte/health
```

## Usage

### Syncing a Candidate to Avionté

#### Via API

```bash
POST /api/avionte/sync/candidate/{candidate_id}?force_update=false
```

#### Via Python

```python
from backend.services.avionte import AvionteClient
from backend.services.avionte.sync import AvionteSyncService
from backend.database.connection import get_db

async def sync_candidate():
    client = AvionteClient()
    async with get_db() as db:
        sync_service = AvionteSyncService(client, db)
        result = await sync_service.sync_candidate_to_avionte(
            candidate_id="your-candidate-id",
            user_id="your-user-id"
        )
        print(result)
```

#### Via Frontend

```typescript
import { avionteService } from '../services/avionteService';

const result = await avionteService.syncCandidate('candidate-id', false);
console.log(result);
```

### Syncing a Job to Avionté

#### Via API

```bash
POST /api/avionte/sync/job/{job_id}?force_update=false
```

#### Via Python

```python
result = await sync_service.sync_job_to_avionte(
    job_id="your-job-id",
    user_id="your-user-id"
)
```

### Batch Sync

Sync multiple candidates or jobs at once:

```bash
POST /api/avionte/sync/batch
Content-Type: application/json

{
  "sync_type": "candidates",
  "candidate_ids": ["id1", "id2", "id3"],
  "force_update": false
}
```

### Syncing from Avionté

Pull a talent from Avionté into the internal system:

```bash
POST /api/avionte/sync/from-avionte/talent/{talent_id}
```

## Data Mapping

### Candidate to Talent Mapping

| Internal Field | Avionté Field | Notes |
|---------------|---------------|-------|
| `name` | `firstName`, `lastName` | Split full name |
| `email` | `email` | Direct mapping |
| `phone` | `phone` | Direct mapping |
| `skills` | `skills[]` | Array transformation |
| `certifications` | `certifications[]` | Array transformation |
| `work_history` | `workHistory[]` | Array transformation |
| `education` | `education[]` | Array transformation |

### Job Mapping

| Internal Field | Avionté Field | Notes |
|---------------|---------------|-------|
| `title` | `jobTitle` | Direct mapping |
| `description` | `description` | Direct mapping |
| `location` | `location` | Direct mapping |
| `required_skills` | `requiredSkills[]` | Array transformation |
| `certifications` | `requiredCertifications[]` | Array transformation |

## Error Handling

The integration handles various error scenarios:

- **Authentication Errors**: Invalid credentials or expired tokens
- **Rate Limiting**: Automatic retry with exponential backoff
- **Network Errors**: Retry logic with configurable attempts
- **Validation Errors**: User-friendly error messages

## Sync Status

The system tracks sync status in the database:

- `avionte_talent_id`: Avionté talent ID (for candidates)
- `avionte_job_id`: Avionté job ID (for jobs)
- `avionte_sync_at`: Last sync timestamp

## Best Practices

1. **Incremental Sync**: Only sync changed records to avoid unnecessary API calls
2. **Batch Operations**: Use batch sync for multiple items
3. **Error Monitoring**: Monitor sync errors and retry failed operations
4. **Rate Limiting**: Respect Avionté API rate limits
5. **Data Validation**: Validate data before syncing to avoid errors

## Troubleshooting

### Authentication Fails

- Verify `AVIONTE_CLIENT_ID` and `AVIONTE_CLIENT_SECRET` are correct
- Check that credentials have not expired
- Verify network access to Avionté API

### Sync Fails

- Check candidate/job exists in database
- Verify data format matches Avionté requirements
- Check API logs for detailed error messages
- Ensure required fields are present

### Rate Limiting

- Reduce sync frequency
- Use batch operations efficiently
- Implement queuing for large sync operations

## API Reference

See `AVIONTE_API_REFERENCE.md` for detailed API endpoint documentation.

## Support

For issues or questions:
1. Check API logs for error details
2. Review Avionté API documentation
3. Contact development team
