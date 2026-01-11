"""Main FastAPI application with modular structure"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel
from app.database import engine
from app.routers import items


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Modular FastAPI Application",
    version="1.0.0",
    description="FastAPI app with modular structure using APIRouter",
    lifespan=lifespan,
)

# Include routers
app.include_router(items.router)


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Welcome to the Modular FastAPI Application"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
