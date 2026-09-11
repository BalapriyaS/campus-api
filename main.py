import os
from fastapi import FastAPI, Depends, HTTPException, status, Query, Security, Header
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from typing import List, Optional
from dotenv import load_dotenv

from database import get_db
import models
import schemas

load_dotenv()

API_KEY = os.getenv("API_KEY", "supersecretkey123")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key


async def get_current_user(x_user_id: str = Header(default="user_1")):
    return x_user_id


app = FastAPI(title="Campus Lost and Found API")


@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "healthy",
        "message": "Campus Lost and Found API is running successfully",
    }


# POST /items - Create Item
@app.post(
    "/items",
    response_model=schemas.ItemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
    tags=["Items"],
)
async def create_item(
    item: schemas.ItemCreate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if item.status.lower() not in ["lost", "found"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be either 'lost' or 'found'.",
        )

    db_item = models.Item(
        title=item.title,
        description=item.description,
        category=item.category,
        location=item.location,
        status=item.status.lower(),
        owner_id=current_user,
    )

    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)

    return db_item


# GET /items - List Items with Search, Filters, and Pagination
@app.get(
    "/items",
    response_model=List[schemas.ItemResponse],
    status_code=status.HTTP_200_OK,
    tags=["Items"],
)
async def get_items(
    q: Optional[str] = Query(None, description="Search term for title or description"),
    status_param: Optional[str] = Query(None, alias="status", description="Filter by status (lost/found)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(models.Item)

    # Filter by status if provided
    if status_param:
        query = query.where(models.Item.status == status_param.lower())

    # Filter by category if provided
    if category:
        query = query.where(models.Item.category.ilike(f"%{category}%"))

    # Search keyword in title or description if provided
    if q:
        search_pattern = f"%{q}%"
        query = query.where(
            or_(
                models.Item.title.ilike(search_pattern),
                models.Item.description.ilike(search_pattern),
            )
        )

    # Deterministic ordering and pagination
    query = query.order_by(models.Item.id.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()
    return items


# GET /items/{item_id} - Fetch Detail
@app.get(
    "/items/{item_id}",
    response_model=schemas.ItemResponse,
    status_code=status.HTTP_200_OK,
    tags=["Items"],
)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    query = select(models.Item).where(models.Item.id == item_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found.",
        )

    return item


# PATCH /items/{item_id} - Partial Update
@app.patch(
    "/items/{item_id}",
    response_model=schemas.ItemResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)],
    tags=["Items"],
)
async def update_item(
    item_id: int,
    item_update: schemas.ItemUpdate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(models.Item).where(models.Item.id == item_id)
    result = await db.execute(query)
    db_item = result.scalar_one_or_none()

    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found.",
        )

    if db_item.owner_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this item.",
        )

    if item_update.status is not None:
        if item_update.status.lower() not in ["lost", "found"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be either 'lost' or 'found'.",
            )
        db_item.status = item_update.status.lower()

    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key != "status":
            setattr(db_item, key, value)

    await db.commit()
    await db.refresh(db_item)

    return db_item


# DELETE /items/{item_id} - Delete Item
@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_api_key)],
    tags=["Items"],
)
async def delete_item(
    item_id: int,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(models.Item).where(models.Item.id == item_id)
    result = await db.execute(query)
    db_item = result.scalar_one_or_none()

    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found.",
        )

    if db_item.owner_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this item.",
        )

    await db.delete(db_item)
    await db.commit()

    return None