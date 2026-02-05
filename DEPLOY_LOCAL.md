# Deploy ResponsAble on Local Server (192.168.5.143)

This guide covers running the app on a local server instead of AWS. The server is expected at **192.168.5.143** with user **crossroadsadmin** (override with `LOCAL_HOST`, `LOCAL_USER` if needed).

---

## 1. Server preparation (once)

- **SSH**: Ensure you can connect: `ssh crossroadsadmin@192.168.5.143`
- **Docker**: Install Docker (and Docker Compose if using the compose option). Add the user to the `docker` group so containers can run without sudo.
- **Directory**: On the server, create a deploy directory, e.g. `/home/crossroadsadmin/responsable`, and put a `.env` file there (see below). Do **not** commit `.env`; it stays only on the server.

---

## 2. Environment file on the server

Create `/home/crossroadsadmin/responsable/.env` (or your chosen `REMOTE_DIR`) with at least:

```bash
# Required: no S3 on local server
USE_S3=false
STORAGE_DIR=storage

# Required: auth signing key (generate with: openssl rand -base64 32)
JWT_SECRET_KEY=<your-random-secret>

# Required for AI features
OPENAI_API_KEY=your-openai-key

# Database (see below for Docker vs compose)
# When using deploy_to_local_server.sh (standalone container): use host that resolves from inside the app container.
#   - If Postgres runs on the host: postgresql://postgres:password@192.168.5.143:5432/candidate_ranker
#   - If Postgres runs in another container on same host: use that container's name as host, or use 192.168.5.143 and expose 5432
# When using docker-compose: DATABASE_URL is set by compose; optionally set POSTGRES_PASSWORD to match (default: responsable_local)
POSTGRES_PASSWORD=responsable_local

# Optional
SESSION_TTL_DAYS=7
# SESSION_SECRET=<random-secret>   # optional, used in AWS; set if needed

# Optional: Avionté
# AVIONTE_CLIENT_ID=...
# AVIONTE_CLIENT_SECRET=...
# AVIONTE_API_BASE_URL=https://api.avionte.com
# AVIONTE_TENANT_ID=...
# AVIONTE_SYNC_ENABLED=false
# AVIONTE_SYNC_INTERVAL=60
```

When using **docker-compose**, you do **not** need to set `DATABASE_URL` in `.env`; the compose file injects it using `POSTGRES_PASSWORD`. When using **standalone** `deploy_to_local_server.sh` (no `--compose`), set `DATABASE_URL` in `.env` to point at your Postgres (e.g. `postgresql://postgres:password@192.168.5.143:5432/candidate_ranker` if Postgres is on the host).

---

## 3. Option A – Deploy with Docker (recommended)

### 3a. Using the deploy script (image transfer)

From your dev machine (repo root):

```bash
# Build image locally and deploy to server (saves image, copies to server, starts container)
./deploy_to_local_server.sh --build
```

The script will:

1. Build the Docker image (with `--build`).
2. Transfer the image to the server (`docker save` | `ssh` | `docker load`).
3. SSH and start the app container with `--env-file` and a volume for `storage`.

Ensure Postgres is already running on the server (e.g. a separate container or native install) and that `.env` contains the correct `DATABASE_URL`.

Subsequent deploys (no local build):

```bash
./deploy_to_local_server.sh
```

(If the image does not exist locally, the script will build it before transferring.)

### 3b. Using docker-compose on the server

From your dev machine, sync the repo and run compose on the server:

```bash
./deploy_to_local_server.sh --build-on-server --compose
```

This rsyncs the project to `/home/crossroadsadmin/responsable/app`, then on the server runs `docker compose up -d --build` from that directory. Compose starts Postgres and the app; `.env` is read from `/home/crossroadsadmin/responsable/.env` (one level above `app`). Use `POSTGRES_PASSWORD` in `.env` (default `responsable_local`); `DATABASE_URL` is set by the compose file.

To only update and restart (no rsync):

```bash
./deploy_to_local_server.sh --compose
```

(Still syncs project; use `--build-on-server --compose` to force a rebuild.)

---

## 4. Option B – Deploy without Docker (native)

- On the server: install **Python 3.11+**, **Node 18+**, and **PostgreSQL**. Create a virtualenv and install backend deps from `backend/requirements.txt`.
- Build the frontend (on the server or locally):  
  `cd frontend && npm ci && npm run build`  
  then copy `frontend/dist` contents into the repo root’s `static` directory (the backend serves from `static` next to `backend/main.py`).
- From repo root, with `.env` in place:  
  `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- Use a systemd unit or similar so the app restarts on reboot.

---

## 5. Verify

- App URL: **http://192.168.5.143:8000**
- Health: `curl http://192.168.5.143:8000/health` → `{"status":"healthy"}`
- Log in and confirm core flows.

---

## 6. Summary

| Method              | Command / steps |
|---------------------|-----------------|
| Deploy script       | `./deploy_to_local_server.sh --build` (ensure Postgres + `.env` with `DATABASE_URL` on server) |
| Deploy + compose    | `./deploy_to_local_server.sh --build-on-server --compose` (`.env` with `POSTGRES_PASSWORD`) |
| Native              | Install Python/Node/Postgres, build frontend, run uvicorn (see Option B). |

See **ENV_TEMPLATE.md** for the full list of environment variables.
