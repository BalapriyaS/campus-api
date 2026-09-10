from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    location: str
    status: str


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    is_claimed: Optional[bool] = None


class ItemResponse(ItemBase):
    id: int
    is_claimed: bool
    owner_id: str
    created_at: datetime

    class Config:
        from_attributes = True