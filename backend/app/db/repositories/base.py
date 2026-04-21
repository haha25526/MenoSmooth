"""
Base Repository - Generic CRUD operations
"""
from typing import Generic, Type, TypeVar, List, Optional, Dict, Any
from sqlalchemy import select, func, exists, Select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Base
from uuid import UUID

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def create(self, db: AsyncSession, obj_in: Dict[str, Any], commit: bool = True) -> ModelType:
        obj = self.model(**obj_in)
        db.add(obj)
        if commit:
            await db.commit()
            await db.refresh(obj)
        return obj

    async def get_by_phone(self, db: AsyncSession, phone: str) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(self.model.phone == phone))
        return result.scalar_one_or_none()
