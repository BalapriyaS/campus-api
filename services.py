from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from fastapi import HTTPException, status
from typing import List, Optional

import models
import schemas


class ItemService:

    @staticmethod
    async def create_item(
        db: AsyncSession, item_data: schemas.ItemCreate, owner_id: str
    ) -> models.Item:
        if item_data.status.lower() not in ["lost", "found"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be either 'lost' or 'found'.",
            )

        db_item = models.Item(
            title=item_data.title,
            description=item_data.description,
            category=item_data.category,
            location=item_data.location,
            status=item_data.status.lower(),
            owner_id=owner_id,
        )
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item

    @staticmethod
    async def get_items(
        db: AsyncSession,
        q: Optional[str] = None,
        status_param: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> List[models.Item]:
        query = select(models.Item)

        if status_param:
            query = query.where(models.Item.status == status_param.lower())
        if category:
            query = query.where(models.Item.category.ilike(f"%{category}%"))
        if q:
            search_pattern = f"%{q}%"
            query = query.where(
                or_(
                    models.Item.title.ilike(search_pattern),
                    models.Item.description.ilike(search_pattern),
                )
            )

        query = query.order_by(models.Item.id.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_item_by_id(db: AsyncSession, item_id: int) -> models.Item:
        query = select(models.Item).where(models.Item.id == item_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_id} not found.",
            )
        return item

    @staticmethod
    async def update_item(
        db: AsyncSession,
        item_id: int,
        item_update: schemas.ItemUpdate,
        current_user: str,
    ) -> models.Item:
        db_item = await ItemService.get_item_by_id(db, item_id)

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

    @staticmethod
    async def delete_item(
        db: AsyncSession, item_id: int, current_user: str
    ) -> None:
        db_item = await ItemService.get_item_by_id(db, item_id)

        if db_item.owner_id != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this item.",
            )

        await db.delete(db_item)
        await db.commit()