"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="Research Assistant API",
    description="AI-powered research assistant for gathering and analyzing information",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "status": "ok",
        "message": "Research Assistant API",
        "version": "0.1.0",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include NLP API routes
from app.api.nlp_routes import router as nlp_router
app.include_router(nlp_router)


# TODO: Add other API routers
# from app.api.v1 import api_router
# app.include_router(api_router, prefix=settings.API_V1_PREFIX)
