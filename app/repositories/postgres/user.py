from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.postgres.base import PostgresRepository


class PostgresUserRepository(PostgresRepository[User]):
    """PostgreSQL implementation of User repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_class=User)

    async def get_active_users(self) -> List[User]:
        """Get all active users."""
        return await self.get_multi(is_active=True)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.filter_one(email=email)
