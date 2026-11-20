from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, CORS_ORIGIN_REGEX
from app.database import engine, Base
import app.models  # Ensures all models (Dataset, Sale, QueryHistory) are registered with Base metadata
from app.routes.health import router as health_router
from app.routes.datasets import router as datasets_router
from app.routes.dashboard import router as dashboard_router
from app.routes.ai import router as ai_router
from app.routes.query_history import router as query_history_router

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter

# Create database tables automatically if they do not already exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="InsightIQ API",
    description="Backend API for InsightIQ AI-Powered Business Intelligence Dashboard",
    version="1.0.0",
)

# Attach rate limiter to application state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers with '/api' prefix
app.include_router(health_router, prefix="/api")
app.include_router(datasets_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(query_history_router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    """Root endpoint welcoming developers and directing to interactive documentation."""
    return {
        "status": "ok",
        "app": "InsightIQ API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "health": "/api/health",
            "database_health": "/api/health/database",
            "datasets": "/api/datasets",
            "upload_csv": "/api/datasets/upload",
            "dashboard_summary": "/api/dashboard/{dataset_id}/summary",
            "ai_generate": "/api/ai/generate-query",
            "ai_execute": "/api/ai/execute-query",
            "ai_explain": "/api/ai/explain-results",
            "query_history": "/api/query-history",
        },
    }
