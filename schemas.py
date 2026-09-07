from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Shared base attributes
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    location: str
    status: str


# Schema for creation (requires all base fields)
class ItemCreate(ItemBase):
    pass


# Schema for updates (all fields optional for partial updates)
class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    is_claimed: Optional[bool] = None


# Schema for responses
class ItemResponse(ItemBase):
    id: int
    is_claimed: bool
    created_at: datetime

    class Config:
        from_attributes = True