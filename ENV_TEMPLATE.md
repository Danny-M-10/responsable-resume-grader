## Environment Variables

Create a `.env` file with:

```
OPENAI_API_KEY=your-openai-key
# DATABASE_URL example for managed Postgres:
# DATABASE_URL=postgresql://user:password@host:port/dbname
# Leave empty to use local SQLite (candidate_ranker.db)
# For ResponsAble application: Uses /responsable-recruitment-ai/DATABASE_URL from SSM
# For internal application: Uses /recruiting-candidate-ranker/DATABASE_URL from SSM
DATABASE_URL=

# Optional storage directory for persisted files (defaults to ./storage)
STORAGE_DIR=storage

# Optional session TTL days (default 7)
SESSION_TTL_DAYS=7

# Avionté API Configuration (optional)
AVIONTE_CLIENT_ID=your-avionte-client-id
AVIONTE_CLIENT_SECRET=your-avionte-client-secret
AVIONTE_API_BASE_URL=https://api.avionte.com
AVIONTE_TENANT_ID=your-tenant-id
AVIONTE_SYNC_ENABLED=false
AVIONTE_SYNC_INTERVAL=60
```

For **local server deployment** (no AWS), see [DEPLOY_LOCAL.md](DEPLOY_LOCAL.md) for a server-specific template and `USE_S3=false`, `STORAGE_DIR`, `JWT_SECRET_KEY`, and database settings.

