from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.db import engine, Base
from app.routers import auth, uploads, jobs, webhooks
from app.utils.metrics import get_metrics_response
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Async File Processing Pipeline",
    description="Resilient, idempotent file processing with resumable uploads and signed webhooks",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(jobs.router)
app.include_router(webhooks.router)


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Async File Processing Pipeline API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics_response()


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )
