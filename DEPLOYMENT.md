## Deployment (Railway / Render)

### Prerequisites
- OpenAI API key (`OPENAI_API_KEY`)
- Git repo accessible to the platform

### Environment
- `OPENAI_API_KEY` (required)
- `DATABASE_URL` (Postgres URL). If omitted, app uses local SQLite (not recommended in production).
- `STORAGE_DIR` (optional, defaults to `storage`)
- `SESSION_TTL_DAYS` (optional, default 7)

### Start Command
The repo includes a `Procfile`:
```
web: streamlit run app_enhanced.py --server.port=$PORT --server.address=0.0.0.0
```

### Database
- Create a managed Postgres instance (Railway/Render).
- Set `DATABASE_URL` env var to the provided connection string.
- Initialize tables (run once):
```
python -c "from db import init_db; init_db()"
```
You can run this as a one-off job on the platform or locally with the same `DATABASE_URL`.

### Deploy on Railway (example)
1. Create a new project, add Postgres plugin.
2. Set env vars: `OPENAI_API_KEY`, `DATABASE_URL` (from plugin), `STORAGE_DIR=storage`.
3. Deploy from the repo; Railway will use `Procfile`.
4. (Optional) Run the one-off migration command above.

### Deploy on Render (example)
1. Create a new Web Service from the repo.
2. Instance type: Starter is fine initially.
3. Build command: `pip install -r requirements.txt`
4. Start command: `streamlit run app_enhanced.py --server.port=$PORT --server.address=0.0.0.0`
5. Add a managed Postgres database, set `DATABASE_URL` from Render’s connection info.
6. Set `OPENAI_API_KEY`, `STORAGE_DIR=storage`.
7. Run the migration command as a Render one-off job.

### Notes
- Files are stored on disk at `STORAGE_DIR`; for true durability, swap `storage.py` to use S3/GCS later.
- Sessions are DB-backed; Streamlit still uses its session state for UI, so keep a single web process for consistency.

