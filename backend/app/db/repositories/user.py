"""
User repository
"""
from app.models.user import User
from app.db.repositories.base import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_phone(self, db: AsyncSession, phone: str) -> User | None:
        result = await db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

user_repository = UserRepository()
