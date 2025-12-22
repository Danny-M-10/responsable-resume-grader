## Environment Variables

Create a `.env` file with:

```
OPENAI_API_KEY=your-openai-key
# DATABASE_URL example for managed Postgres:
# DATABASE_URL=postgresql://user:password@host:port/dbname
# Leave empty to use local SQLite (candidate_ranker.db)
DATABASE_URL=

# Optional storage directory for persisted files (defaults to ./storage)
STORAGE_DIR=storage

# Optional session TTL days (default 7)
SESSION_TTL_DAYS=7
```

