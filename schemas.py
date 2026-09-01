from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ItemBase(BaseModel):
    title: str = Field(..., example="Blue Backpack")
    description: str = Field(..., example="Left near library table 3, contains notebooks")
    category: str = Field(..., example="Electronics")
    location: str = Field(..., example="Central Library")
    status: str = Field(..., example="lost") 


class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None

class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    is_claimed: bool = False

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    detail: str