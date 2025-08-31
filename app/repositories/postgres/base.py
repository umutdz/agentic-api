from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import BaseModel
from app.repositories.interfaces.base import IRepository

T = TypeVar("T", bound=BaseModel)


class PostgresRepository(IRepository[T], Generic[T]):
    """
    PostgreSQL implementation of the repository pattern.
    All PostgreSQL repository classes should inherit from this class.
    """

    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self.session = session
        self.model_class = model_class

    async def create(self, obj_in: dict) -> T:
        """Create a new record in the database."""
        try:
            db_obj = self.model_class(**obj_in)
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            return db_obj
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get(self, id: int) -> Optional[T]:
        """Get a single record by id."""
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(self, *, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Get multiple records with optional filtering and pagination."""
        query = select(self.model_class)

        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, id: Any, obj_in: dict) -> Optional[T]:
        """Update a record."""
        try:
            query = update(self.model_class).where(self.model_class.id == id).values(**obj_in).returning(self.model_class)
            result = await self.session.execute(query)
            await self.session.flush()
            await self.session.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            raise e

    async def delete(self, id: Any) -> bool:
        """Delete a record."""
        try:
            query = delete(self.model_class).where(self.model_class.id == id)
            result = await self.session.execute(query)
            await self.session.flush()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            raise e

    async def exists(self, **filters) -> bool:
        """Check if a record exists with given filters."""
        query = select(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def filter_one(self, **filters) -> Optional[T]:
        """Filter records with given filters."""
        query = select(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    def with_relationships(self, *relationships: str):
        """Add relationships to the query for eager loading."""
        return selectinload(*relationships)
