import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status, Query, Security, Header, Request
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from dotenv import load_dotenv

from database import get_db
import schemas
from services import ItemService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("campus_api")

load_dotenv()

API_KEY = os.getenv("API_KEY", "supersecretkey123")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        logger.warning("Failed API Key authorization attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key


async def get_current_user(x_user_id: str = Header(default="user_1")):
    return x_user_id


app = FastAPI(title="Campus Lost and Found API")


# Global Exception Handler for Unhandled Errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error occurred on route {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please try again later."},
    )


@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "healthy",
        "message": "Campus Lost and Found API is running successfully",
    }


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
    return await ItemService.create_item(db, item, current_user)


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
    return await ItemService.get_items(db, q, status_param, category, skip, limit)


@app.get(
    "/items/{item_id}",
    response_model=schemas.ItemResponse,
    status_code=status.HTTP_200_OK,
    tags=["Items"],
)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    return await ItemService.get_item_by_id(db, item_id)


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
    return await ItemService.update_item(db, item_id, item_update, current_user)


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
    await ItemService.delete_item(db, item_id, current_user)
    return None