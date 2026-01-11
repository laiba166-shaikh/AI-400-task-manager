"""
Script to generate CRUD endpoint template code for a FastAPI resource.

Usage:
    python generate_crud_endpoints.py ResourceName

Example:
    python generate_crud_endpoints.py Product

This will print CRUD endpoint code for a Product resource that you can
copy into your FastAPI router file.
"""

import sys


def generate_crud_endpoints(resource_name: str) -> str:
    """Generate CRUD endpoint template for a resource"""
    resource_lower = resource_name.lower()
    resource_plural = f"{resource_lower}s"  # Simple pluralization

    template = f'''"""
{resource_name} CRUD Router
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.database import SessionDep
from app.models.{resource_lower} import {resource_name}
from app.schemas.{resource_lower} import {resource_name}Create, {resource_name}Update, {resource_name}Response

router = APIRouter(prefix="/{resource_plural}", tags=["{resource_plural}"])


@router.post("/", response_model={resource_name}Response, status_code=status.HTTP_201_CREATED)
def create_{resource_lower}({resource_lower}: {resource_name}Create, session: SessionDep):
    """Create a new {resource_lower}"""
    db_{resource_lower} = {resource_name}.model_validate({resource_lower})
    session.add(db_{resource_lower})
    session.commit()
    session.refresh(db_{resource_lower})
    return db_{resource_lower}


@router.get("/", response_model=list[{resource_name}Response])
def list_{resource_plural}(session: SessionDep, skip: int = 0, limit: int = 100):
    """List all {resource_plural} with pagination"""
    {resource_plural} = session.exec(select({resource_name}).offset(skip).limit(limit)).all()
    return {resource_plural}


@router.get("/{{{{id}}}}", response_model={resource_name}Response)
def read_{resource_lower}(id: int, session: SessionDep):
    """Get a specific {resource_lower} by ID"""
    {resource_lower} = session.get({resource_name}, id)
    if not {resource_lower}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{resource_name} not found"
        )
    return {resource_lower}


@router.patch("/{{{{id}}}}", response_model={resource_name}Response)
def update_{resource_lower}(id: int, {resource_lower}: {resource_name}Update, session: SessionDep):
    """Update an existing {resource_lower}"""
    db_{resource_lower} = session.get({resource_name}, id)
    if not db_{resource_lower}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{resource_name} not found"
        )

    {resource_lower}_data = {resource_lower}.model_dump(exclude_unset=True)
    db_{resource_lower}.sqlmodel_update({resource_lower}_data)

    session.add(db_{resource_lower})
    session.commit()
    session.refresh(db_{resource_lower})
    return db_{resource_lower}


@router.delete("/{{{{id}}}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_{resource_lower}(id: int, session: SessionDep):
    """Delete a {resource_lower}"""
    {resource_lower} = session.get({resource_name}, id)
    if not {resource_lower}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{resource_name} not found"
        )
    session.delete({resource_lower})
    session.commit()
    return None
'''
    return template


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_crud_endpoints.py ResourceName")
        print("Example: python generate_crud_endpoints.py Product")
        sys.exit(1)

    resource_name = sys.argv[1]

    # Validate resource name
    if not resource_name.isalpha() or not resource_name[0].isupper():
        print("Error: Resource name must be PascalCase (e.g., Product, UserProfile)")
        sys.exit(1)

    code = generate_crud_endpoints(resource_name)
    print(code)
    print(f"\n# Copy the above code to app/routers/{resource_name.lower()}.py")


if __name__ == "__main__":
    main()
