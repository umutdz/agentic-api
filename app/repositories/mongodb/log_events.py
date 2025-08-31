from typing import List

from app.repositories.mongodb.base import MongoDBRepository
from app.schemas.logs import LogEvent


class LogEventsRepository(MongoDBRepository[LogEvent]):
    """
    Mongo 'log_events' koleksiyonu için repository.
    _id <-> event_id eşlemesi yapar; kronolojik listeleme sağlar.
    """

    def __init__(self, collection_name: str = "log_events") -> None:
        super().__init__(
            model=LogEvent,
            collection_name=collection_name,
            to_mongo=self._to_mongo,
            from_mongo=self._from_mongo,
            id_field="_id",
        )

    # ------------- mapping helpers -------------
    @staticmethod
    def _to_mongo(obj: LogEvent | dict) -> dict:
        if isinstance(obj, LogEvent):
            d = obj.model_dump(exclude_none=True)
        else:
            # dict gelirse yine None değerleri eliyoruz (protection)
            d = {k: v for k, v in dict(obj).items() if v is not None}

        # event_id -> _id (only if truthy)
        event_id = d.pop("event_id", None)
        if event_id:
            d["_id"] = event_id

        return d

    @staticmethod
    def _from_mongo(doc: dict) -> LogEvent:
        d = dict(doc)
        if "_id" in d:
            d["event_id"] = str(d.pop("_id"))
        if hasattr(LogEvent, "model_validate"):
            return LogEvent.model_validate(d)  # type: ignore[attr-defined]
        return LogEvent(**d)

    # ------------- domain methods -------------

    async def push(self, event: LogEvent) -> str:
        created = await self.create(event)
        # event_id mapping from _from_mongo
        return created.event_id or ""  # type: ignore[return-value]

    async def list_by_job(self, job_id: str, limit: int = 200) -> List[LogEvent]:
        return await self.get_multi(
            limit=int(limit),
            sort=[("ts", 1)],
            job_id=job_id,
        )

    # ------------- indexes (opsiyonel helper) -------------

    @staticmethod
    async def ensure_indexes(db) -> None:
        log_events = db.get_collection("log_events")
        await log_events.create_index([("job_id", 1), ("ts", 1)], name="job_ts")
        await log_events.create_index([("type", 1), ("ts", -1)], name="type_ts")
