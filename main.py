"""FastAPI application entry point with SQLModel."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel
from app.database import init_db
from app.routers import tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database connection and create tables
    - Shutdown: Dispose database engine

    This ensures tables are created from SQLModel metadata
    and connections are properly closed on shutdown.
    """
    # Startup: Initialize database and create tables
    engine = init_db()

    async with engine.begin() as conn:
        # Create all tables defined in SQLModel metadata
        # This will create the 'tasks' table with all fields
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Shutdown: Dispose engine and close connections
    await engine.dispose()


app = FastAPI(
    title="Task Manager API",
    version="1.0.0",
    description="Simple CRUD API for managing tasks using SQLModel",
    lifespan=lifespan,
)

# Include routers
app.include_router(tasks.router)


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint.

    Returns:
        Welcome message with API version

    Example Response:
        {
            "message": "Task Manager API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    """
    return {
        "message": "Task Manager API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Used for monitoring and load balancer health checks.

    Returns:
        Health status

    Example Response:
        {
            "status": "healthy"
        }
    """
    return {"status": "healthy"}
