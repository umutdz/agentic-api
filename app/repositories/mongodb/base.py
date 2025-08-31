import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from app.db.mongodb.mongodb import MongoDB
from app.repositories.interfaces.base import IRepository

T = TypeVar("T", bound=BaseModel)


class MongoDBRepository(IRepository[T]):
    """
    Base MongoDB repository implementation.
    """

    def __init__(
        self,
        model: Type[T],
        collection_name: str,
        *,
        to_mongo: Optional[Callable[[T | Dict[str, Any]], Dict[str, Any]]] = None,
        from_mongo: Optional[Callable[[Dict[str, Any]], T]] = None,
        id_field: str = "_id",
    ):
        self.model = model
        self.collection_name = collection_name
        self.collection = None
        self.logger = logging.getLogger(__name__)
        self._to_mongo = to_mongo
        self._from_mongo = from_mongo
        self.id_field = id_field

    # ---------- helpers ----------

    async def _get_collection(self):
        """Get MongoDB collection (lazy)."""
        try:
            if self.collection is None:
                db = await MongoDB.get_database()
                self.collection = db[self.collection_name]
                self.logger.info("Connected to collection: %s", self.collection_name)
            return self.collection
        except Exception as e:
            self._raise("Failed to get collection %s: %s", self.collection_name, e)

    def _model_from_dict(self, doc: Optional[Dict[str, Any]]) -> Optional[T]:
        if not doc:
            return None
        if self._from_mongo:
            return self._from_mongo(doc)
        # pydantic v2 prefer
        if hasattr(self.model, "model_validate"):
            return self.model.model_validate(doc)  # type: ignore[attr-defined]
        return self.model(**doc)

    def _dict_from_input(self, obj_in: T | Dict[str, Any]) -> Dict[str, Any]:
        if self._to_mongo:
            return self._to_mongo(obj_in)
        if isinstance(obj_in, BaseModel):
            # pydantic v2 .model_dump / v1 .dict
            if hasattr(obj_in, "model_dump"):
                return obj_in.model_dump()  # type: ignore[attr-defined]
            return obj_in.dict()  # type: ignore[call-arg]
        return dict(obj_in)

    def _raise(self, msg: str, *args):
        text = msg % args if args else msg
        self.logger.error(text)
        raise RuntimeError(text)

    # ---------- IRepository impl ----------

    async def create(self, obj_in: Dict[str, Any] | T) -> T:
        """Create a new record in MongoDB."""
        try:
            collection = await self._get_collection()
            doc = self._dict_from_input(obj_in)
            result = await collection.insert_one(doc)
            # _id yoksa Mongo ObjectId atar; normalize etmek isterseniz burada stringe çevirebilirsiniz
            if self.id_field not in doc:
                doc[self.id_field] = str(result.inserted_id)
            # created obj'u geri döndür
            return self._model_from_dict(doc)  # type: ignore[return-value]
        except Exception as e:
            self._raise("Failed to create record: %s", e)

    async def get(self, id: Any) -> Optional[T]:
        """Get a single record by id."""
        try:
            collection = await self._get_collection()
            doc = await collection.find_one({self.id_field: id})
            return self._model_from_dict(doc)
        except Exception as e:
            self._raise("Failed to get record: %s", e)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None,
        projection: Optional[Dict[str, int]] = None,
        **filters: Any,
    ) -> List[T]:
        """Get multiple records with optional filtering, sorting, projection and pagination."""
        try:
            collection = await self._get_collection()
            cursor = collection.find(filters or {}, projection=projection).skip(int(skip)).limit(int(limit))
            if sort:
                cursor = cursor.sort(sort)
            items: List[T] = []
            async for doc in cursor:
                model = self._model_from_dict(doc)
                if model is not None:
                    items.append(model)
            return items
        except Exception as e:
            self._raise("Failed to get multiple records: %s", e)

    async def update(self, id: Any, obj_in: dict) -> Optional[T]:
        """Update a record (partial)."""
        try:
            collection = await self._get_collection()
            await collection.update_one({self.id_field: id}, {"$set": dict(obj_in)})
            doc = await collection.find_one({self.id_field: id})
            return self._model_from_dict(doc)
        except Exception as e:
            self._raise("Failed to update record: %s", e)

    async def delete(self, id: Any) -> bool:
        """Delete a record."""
        try:
            collection = await self._get_collection()
            res = await collection.delete_one({self.id_field: id})
            return res.deleted_count > 0
        except Exception as e:
            self._raise("Failed to delete record: %s", e)

    async def exists(self, **filters: Any) -> bool:
        """Check if a record exists with given filters (efficient)."""
        try:
            collection = await self._get_collection()
            doc = await collection.find_one(filters or {}, projection={self.id_field: 1})
            return doc is not None
        except Exception as e:
            self._raise("Failed to check record existence: %s", e)

    async def filter_one(self, **filters: Any) -> Optional[T]:
        """Filter records with given filters."""
        try:
            collection = await self._get_collection()
            doc = await collection.find_one(filters or {})
            return self._model_from_dict(doc)
        except Exception as e:
            self._raise("Failed to filter records: %s", e)
