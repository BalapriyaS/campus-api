from fastapi import FastAPI, HTTPException, status
from typing import List
from schemas import ItemCreate, ItemResponse, ItemUpdate, ErrorResponse

app = FastAPI(title="Campus Lost and Found API")

# Temporary in-memory database store for Day 2 mockup
items_db = []

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy", "message": "Campus Lost and Found API is running successfully"}

# 1. Create Item
@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, tags=["Items"])
def create_item(item: ItemCreate):
    new_item = {
        "id": len(items_db) + 1,
        **item.model_dump(),
        "created_at": "2026-09-01T10:00:00",
        "is_claimed": False
    }
    items_db.append(new_item)
    return new_item

# 2. Get All Items
@app.get("/items", response_model=List[ItemResponse], tags=["Items"])
def get_items():
    return items_db

# 3. Get Single Item by ID
@app.get("/items/{item_id}", response_model=ItemResponse, responses={404: {"model": ErrorResponse}}, tags=["Items"])
def get_item(item_id: int):
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")