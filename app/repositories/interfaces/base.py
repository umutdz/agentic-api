from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class IRepository(Generic[T], ABC):
    """Base repository interface that defines the contract for all repositories."""

    @abstractmethod
    async def create(self, obj_in: dict) -> T:
        """Create a new record in the database."""

    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """Get a single record by id."""

    @abstractmethod
    async def get_multi(self, *, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Get multiple records with optional filtering and pagination."""

    @abstractmethod
    async def update(self, id: Any, obj_in: dict) -> Optional[T]:
        """Update a record."""

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete a record."""

    @abstractmethod
    async def exists(self, **filters) -> bool:
        """Check if a record exists with given filters."""

    @abstractmethod
    async def filter_one(self, **filters) -> Optional[T]:
        """Filter records with given filters."""
