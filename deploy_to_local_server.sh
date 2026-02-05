#!/bin/bash
# Deploy ResponsAble application to local server (192.168.5.143).
# Builds image (optional), transfers to server, restarts the app container.
# Does NOT overwrite .env or storage on the server; ensure .env exists there once.

set -e

# Configuration
LOCAL_HOST="${LOCAL_HOST:-192.168.5.143}"
LOCAL_USER="${LOCAL_USER:-crossroadsadmin}"
REMOTE_DIR="${REMOTE_DIR:-/home/crossroadsadmin/responsable}"
IMAGE_NAME="responsable-app:latest"

# Options
BUILD_LOCAL=false
BUILD_ON_SERVER=false
USE_COMPOSE=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "  --build          Build Docker image locally before deploying"
    echo "  --build-on-server Rsync repo to server and build image there (no image transfer)"
    echo "  --compose        On server, run 'docker compose up -d' instead of standalone docker run"
    echo "  -h, --help       Show this help"
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        --build)          BUILD_LOCAL=true ;;
        --build-on-server) BUILD_ON_SERVER=true ;;
        --compose)        USE_COMPOSE=true ;;
        -h|--help)        usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
    shift
done

SSH_TARGET="${LOCAL_USER}@${LOCAL_HOST}"

echo "=========================================="
echo "Deploy ResponsAble to local server"
echo "=========================================="
echo "Target: $SSH_TARGET"
echo "Remote dir: $REMOTE_DIR"
echo ""

# Step 1: Optional local build
if [ "$BUILD_LOCAL" = true ]; then
    echo "Step 1: Building Docker image locally..."
    if ! docker build -t "$IMAGE_NAME" .; then
        echo "✗ Docker build failed"
        exit 1
    fi
    echo "✓ Image built"
    echo ""
fi

# Step 2a: Transfer image to server (save -> scp -> load)
if [ "$USE_COMPOSE" = true ]; then
    echo "Step 2: Syncing project to server for docker compose..."
    rsync -avz --delete \
        --exclude '.git' \
        --exclude 'node_modules' \
        --exclude 'frontend/node_modules' \
        --exclude '__pycache__' \
        --exclude '.env' \
        --exclude 'storage' \
        --exclude '*.db' \
        --exclude '.cursor' \
        . "${SSH_TARGET}:${REMOTE_DIR}/app/"
    ssh "$SSH_TARGET" "mkdir -p ${REMOTE_DIR}/storage"
    echo "✓ Project synced"
elif [ "$BUILD_ON_SERVER" = true ]; then
    echo "Step 2: Rsyncing project to server (will build there)..."
    rsync -avz --delete \
        --exclude '.git' \
        --exclude 'node_modules' \
        --exclude 'frontend/node_modules' \
        --exclude '__pycache__' \
        --exclude '.env' \
        --exclude 'storage' \
        --exclude '*.db' \
        --exclude '.cursor' \
        . "${SSH_TARGET}:${REMOTE_DIR}/app/"
    ssh "$SSH_TARGET" "mkdir -p ${REMOTE_DIR}/storage"
    echo "Step 2b: Building image on server..."
    ssh "$SSH_TARGET" "cd ${REMOTE_DIR}/app && docker build -t ${IMAGE_NAME} ."
    echo "✓ Build on server complete"
else
    # Ensure we have an image (build if not already built)
    if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
        echo "Step 1: Building Docker image (no image found)..."
        docker build -t "$IMAGE_NAME" .
    fi
    echo "Step 2: Transferring image to server..."
    docker save "$IMAGE_NAME" | ssh "$SSH_TARGET" "docker load"
    echo "✓ Image transferred"
fi
echo ""

# Step 3: Ensure remote dir and .env exist (warn only)
ssh "$SSH_TARGET" "mkdir -p ${REMOTE_DIR} ${REMOTE_DIR}/storage"
if ! ssh "$SSH_TARGET" "test -f ${REMOTE_DIR}/.env" 2>/dev/null; then
    echo "⚠ Warning: ${REMOTE_DIR}/.env not found on server."
    echo "  Create it with DATABASE_URL, USE_S3=false, STORAGE_DIR, JWT_SECRET_KEY, OPENAI_API_KEY."
    echo "  See DEPLOY_LOCAL.md for a template."
    if [ "$USE_COMPOSE" = false ]; then
        read -p "Continue anyway? (y/N) " -n 1 -r; echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi
    fi
fi

# Step 4: Start or restart app on server
if [ "$USE_COMPOSE" = true ]; then
    echo "Step 4: Running docker compose on server..."
    ssh "$SSH_TARGET" "cd ${REMOTE_DIR}/app && docker compose up -d --build"
    echo "✓ Compose up done"
else
    echo "Step 4: Restarting app container..."
    ssh "$SSH_TARGET" "docker stop responsable-app 2>/dev/null || true; docker rm responsable-app 2>/dev/null || true"
    ssh "$SSH_TARGET" "docker run -d --name responsable-app --restart unless-stopped -p 8000:8000 --env-file ${REMOTE_DIR}/.env -v ${REMOTE_DIR}/storage:/app/storage ${IMAGE_NAME}"
    echo "✓ Container started"
fi
echo ""

echo "=========================================="
echo "Deploy complete"
echo "=========================================="
echo "App URL: http://${LOCAL_HOST}:8000"
echo "Health:  curl http://${LOCAL_HOST}:8000/health"
echo ""
