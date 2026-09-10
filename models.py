from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, nullable=False)  # "lost" or "found"
    is_claimed = Column(Boolean, default=False)
    owner_id = Column(String, nullable=False, default="user_1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())