"""
FastAPI CRUD Example - Single File with Database

Complete CRUD API with SQLModel and SQLite database.
Run with: fastapi dev main.py
"""

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, status
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Annotated

# Database Models
class ItemBase(SQLModel):
    """Base model for Item with shared fields"""

    name: str = Field(index=True, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(gt=0, description="Price must be greater than 0")
    tax: float | None = Field(default=None, ge=0, le=1, description="Tax rate (0-1)")


class Item(ItemBase, table=True):
    """Database table model for Item"""

    id: int | None = Field(default=None, primary_key=True)


class ItemCreate(ItemBase):
    """Request model for creating items"""

    pass


class ItemUpdate(SQLModel):
    """Request model for updating items (all fields optional)"""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    price: float | None = Field(None, gt=0)
    tax: float | None = Field(None, ge=0, le=1)


class ItemResponse(ItemBase):
    """Response model for items"""

    id: int


# Database Setup
DATABASE_URL = "sqlite:///./database.db"

connect_args = {"check_same_thread": False}  # Only for SQLite
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=True)


def create_db_and_tables():
    """Initialize database and create tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency to provide database session"""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    create_db_and_tables()
    yield


app = FastAPI(
    title="Item CRUD API",
    version="1.0.0",
    description="Simple CRUD API for managing items",
    lifespan=lifespan,
)


# CRUD Endpoints
@app.post(
    "/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED
)
def create_item(item: ItemCreate, session: SessionDep):
    """
    Create a new item

    - **name**: Item name (required)
    - **description**: Item description (optional)
    - **price**: Item price (required, must be > 0)
    - **tax**: Tax rate (optional, 0-1)
    """
    db_item = Item.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@app.get("/items/", response_model=list[ItemResponse])
def list_items(
    session: SessionDep, skip: int = 0, limit: int = 100
):
    """
    Retrieve a list of items

    - **skip**: Number of items to skip (pagination)
    - **limit**: Maximum number of items to return (max 100)
    """
    items = session.exec(select(Item).offset(skip).limit(limit)).all()
    return items


@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, session: SessionDep):
    """
    Retrieve a specific item by ID

    Returns 404 if item not found
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return item


@app.patch("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemUpdate, session: SessionDep):
    """
    Update an existing item (partial update)

    Only provided fields will be updated.
    Returns 404 if item not found.
    """
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )

    # Update only provided fields
    item_data = item.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(item_data)

    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, session: SessionDep):
    """
    Delete an item by ID

    Returns 404 if item not found.
    Returns 204 No Content on success.
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    session.delete(item)
    session.commit()
    return None
