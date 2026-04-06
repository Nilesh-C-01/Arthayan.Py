from fastapi import FastAPI
from app.core.config import settings
from app.models.database import engine, Base
from app.models.domain import User

# Essential: Import the API router to connect application endpoints
from app.api.routes.api import router as api_router

# Initialize and create database tables if they do not exist
Base.metadata.create_all(bind=engine)

# Instantiate the FastAPI application with project settings
app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

@app.get("/health")
def health_check():
    """Endpoint to verify if the core application engine is running."""
    return {"status": "Production Engine is Running!", "version": settings.PROJECT_VERSION}

# Register the API routes (Login, Dashboard, Transactions) to the main application
app.include_router(api_router)