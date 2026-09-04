from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
import models
import schemas

app = FastAPI(title="Campus Lost and Found API")


@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "healthy",
        "message": "Campus Lost and Found API is running successfully",
    }


# POST /items - Create Item with Transactional Write & Validation
@app.post(
    "/items",
    response_model=schemas.ItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Items"],
)
async def create_item(
    item: schemas.ItemCreate, db: AsyncSession = Depends(get_db)
):
    # Field Validation: Ensure status is either 'lost' or 'found'
    if item.status.lower() not in ["lost", "found"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be either 'lost' or 'found'.",
        )

    # Convert Pydantic schema to SQLAlchemy database model instance
    db_item = models.Item(
        title=item.title,
        description=item.description,
        category=item.category,
        location=item.location,
        status=item.status.lower(),
    )

    # Persist object inside a transactional session
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)

    return db_item