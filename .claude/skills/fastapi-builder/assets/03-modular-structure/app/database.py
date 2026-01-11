"""Database configuration and session management"""

from sqlmodel import create_engine, Session
from typing import Annotated
from fastapi import Depends

DATABASE_URL = "sqlite:///./database.db"

connect_args = {"check_same_thread": False}  # Only for SQLite
engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)


def get_session():
    """Provides database session via dependency injection"""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
