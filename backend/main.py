"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from backend.database.connection import init_db, close_db
from backend.database.init_db_async import init_db_async
from backend.api import auth, jobs, resumes, candidates, analysis, reports, templates, settings, vault, chat
from backend.websocket import progress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting up FastAPI application...")
    await init_db()
    # Initialize database tables - CRITICAL: Must succeed
    try:
        logger.info("Initializing database tables...")
        await init_db_async()
        logger.info("✓ Database tables initialized successfully")
    except Exception as e:
        logger.error(f"✗ CRITICAL: Failed to initialize database tables: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Don't fail startup, but log the error prominently
        # Tables might already exist, or we need to fix the issue
    logger.info("FastAPI application started successfully")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="ResponsAble - Candidate Ranking API",
    description="Safety Staffing on Demand API",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=True  # Automatically redirect trailing slashes
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev server
        "http://localhost:5174",  # Alternative Vite port
        "https://recruiting.crossroadcoach.com",  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for validation errors (422) to log details
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # #region agent log
    logger.error(f"[HYP-E] RequestValidationError on {request.method} {request.url.path}")
    logger.error(f"[HYP-E] Validation errors: {exc.errors()}")
    logger.error(f"[HYP-E] Request URL: {request.url}")
    logger.error(f"[HYP-E] Request headers: {dict(request.headers)}")
    # #endregion
    return await request_validation_exception_handler(request, exc)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(vault.router, prefix="/api/vault", tags=["vault"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# WebSocket routes
from fastapi import WebSocket as WS, Query

@app.websocket("/ws/progress")
async def websocket_progress(websocket: WS, client_id: str = Query("default")):
    """WebSocket endpoint for progress updates"""
    await progress.websocket_endpoint(websocket, client_id)


# Serve static files (React frontend)
static_dir = Path(__file__).parent.parent / "static"
assets_dir = static_dir / "assets"

# Mount assets directory for CSS, JS, and other static assets from Vite build
app.mount("/assets", StaticFiles(directory=str(assets_dir), check_dir=False), name="assets")

# Serve other static files from root (like vite.svg)
vite_svg_path = static_dir / "vite.svg"

@app.get("/vite.svg")
async def serve_vite_svg():
    if vite_svg_path.exists():
        return FileResponse(str(vite_svg_path))
    return JSONResponse({"error": "Not found"}, status_code=404)

favicon_path = static_dir / "favicon.ico"

@app.get("/favicon.ico")
async def serve_favicon():
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    return JSONResponse({"error": "Not found"}, status_code=404)


@app.get("/")
async def root():
    """Root endpoint - serve React app"""
    index_path = static_dir / "index.html"
    if static_dir.exists() and index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({
        "message": "ResponsAble - Candidate Ranking API",
        "version": "1.0.0",
        "status": "running"
    })


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy"})


# Catch-all route for React Router (serve index.html for all non-API routes)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all non-API routes"""
    # Don't interfere with API routes, WebSocket routes, health check, or static assets
    # Note: vite.svg and favicon.ico are handled by dedicated handlers above, so don't block them here
    if (full_path.startswith("api/") or 
        full_path.startswith("ws/") or 
        full_path.startswith("assets/") or
        full_path == "health" or
        full_path == "robots.txt"):
        return JSONResponse({"error": "Not found"}, status_code=404)
    
    index_path = static_dir / "index.html"
    if static_dir.exists() and index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({"error": "Frontend not found"}, status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

