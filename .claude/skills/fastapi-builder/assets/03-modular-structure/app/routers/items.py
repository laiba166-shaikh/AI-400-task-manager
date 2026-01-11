"""Item router with CRUD endpoints"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.database import SessionDep
from app.models import Item
from app.schemas import ItemCreate, ItemUpdate, ItemResponse

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, session: SessionDep):
    """Create a new item"""
    db_item = Item.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.get("/", response_model=list[ItemResponse])
def list_items(session: SessionDep, skip: int = 0, limit: int = 100):
    """List all items with pagination"""
    items = session.exec(select(Item).offset(skip).limit(limit)).all()
    return items


@router.get("/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, session: SessionDep):
    """Get a specific item by ID"""
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return item


@router.patch("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemUpdate, session: SessionDep):
    """Update an existing item"""
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    item_data = item.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(item_data)

    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, session: SessionDep):
    """Delete an item"""
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    session.delete(item)
    session.commit()
    return None
