"""
FastAPI Hello World - Minimal Example

This is the simplest possible FastAPI application.
Run with: fastapi dev main.py
"""

from fastapi import FastAPI

app = FastAPI(title="Hello World API", version="1.0.0")


@app.get("/")
async def root():
    """Root endpoint returning a welcome message"""
    return {"message": "Hello World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """
    Example endpoint with path and query parameters

    - item_id: Path parameter (integer)
    - q: Optional query parameter (string)
    """
    return {"item_id": item_id, "q": q}
