"""
Main application entry point for the Resume ATS Optimizer API.

This module initializes the FastAPI application, configures CORS,
and registers all API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import resume

app = FastAPI(
    title="Resume ATS Optimizer API",
    description="AI-powered API for parsing, optimizing, and managing resumes for ATS systems",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router, prefix="/api/v1")


@app.get("/")
def root():
    """Root endpoint returning API status."""
    return {
        "message": "Resume ATS Optimizer API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
