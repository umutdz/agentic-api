from datetime import datetime, timezone
from typing import Optional

from app.repositories.mongodb.base import MongoDBRepository
from app.schemas.jobs import JobDoc, JobError, JobResult, JobStatusEnum

# State machine rules
ALLOWED_TRANSITIONS = {
    JobStatusEnum.queued: {JobStatusEnum.running, JobStatusEnum.canceled},
    JobStatusEnum.running: {JobStatusEnum.succeeded, JobStatusEnum.failed, JobStatusEnum.canceled},
    JobStatusEnum.succeeded: set(),
    JobStatusEnum.failed: set(),
    JobStatusEnum.canceled: set(),
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class JobsRepository(MongoDBRepository[JobDoc]):
    """
    Domain-specific repository for Mongo 'jobs' collection.

    Notes:
    - _id field is mapped to string 'job_id'.
    - transition/succeed/fail atomic updates.
    - succeed/fail only happens when status is queued|running (race condition protection).
    """

    def __init__(self, collection_name: str = "jobs") -> None:
        super().__init__(
            model=JobDoc,
            collection_name=collection_name,
            to_mongo=self._to_mongo,
            from_mongo=self._from_mongo,
            id_field="_id",
        )

    # ------------- mapping helpers -------------

    @staticmethod
    def _to_mongo(obj: JobDoc | dict) -> dict:
        # Pydantic or dict
        if isinstance(obj, JobDoc):
            d = obj.model_dump()
        else:
            d = dict(obj)

        # job_id -> _id
        if "job_id" in d:
            d["_id"] = d.pop("job_id")

        # Enum to string
        if "status" in d and isinstance(d["status"], JobStatusEnum):
            d["status"] = d["status"].value

        # timestamps default values
        d.setdefault("created_at", _now())
        d.setdefault("updated_at", _now())
        return d

    @staticmethod
    def _from_mongo(doc: dict) -> JobDoc:
        d = dict(doc)
        if "_id" in d:
            d["job_id"] = str(d.pop("_id"))
        # string status to enum
        if "status" in d and isinstance(d["status"], str):
            try:
                d["status"] = JobStatusEnum(d["status"])
            except ValueError:
                pass
        # pydantic v2 support
        if hasattr(JobDoc, "model_validate"):
            return JobDoc.model_validate(d)  # type: ignore[attr-defined]
        return JobDoc(**d)

    # ------------- domain methods -------------

    async def create_job(self, job: JobDoc) -> str:
        created = await self.create(job)
        return created.job_id  # type: ignore[return-value]

    async def get_by_idempotency(self, idempotency_key: str, task_hash: str) -> Optional[JobDoc]:
        return await self.filter_one(idempotency_key=idempotency_key, task_hash=task_hash)

    async def transition(
        self,
        job_id: str,
        to: JobStatusEnum,
        *,
        expected_from: Optional[JobStatusEnum] = None,
    ) -> bool:
        """
        Atomic state transition. If expected_from is provided, guard is applied.
        """
        # Transition rule
        if expected_from and to not in ALLOWED_TRANSITIONS[expected_from]:
            return False

        coll = await self._get_collection()
        filt = {"_id": job_id}
        if expected_from:
            filt["status"] = expected_from.value

        res = await coll.update_one(filt, {"$set": {"status": to.value, "updated_at": _now()}})
        return res.modified_count == 1

    async def set_decision(self, job_id: str, *, agent: str, reason: str) -> None:
        coll = await self._get_collection()
        await coll.update_one(
            {"_id": job_id},
            {"$set": {"decided_agent": agent, "reason": reason, "updated_at": _now()}},
        )

    async def progress(self, job_id: str, value: float) -> None:
        v = max(0.0, min(1.0, float(value)))
        coll = await self._get_collection()
        await coll.update_one({"_id": job_id}, {"$set": {"progress": v, "updated_at": _now()}})

    async def set_attempts_inc(self, job_id: str, by: int = 1) -> None:
        coll = await self._get_collection()
        await coll.update_one({"_id": job_id}, {"$inc": {"attempts": int(by)}, "$set": {"updated_at": _now()}})

    async def succeed(self, job_id: str, result: JobResult) -> bool:
        """
        queued|running -> succeeded
        """

        payload = result.model_dump(mode="json")

        coll = await self._get_collection()
        res = await coll.update_one(
            {"_id": job_id, "status": {"$in": [JobStatusEnum.queued.value, JobStatusEnum.running.value]}},
            {
                "$set": {
                    "status": JobStatusEnum.succeeded.value,
                    "result": payload,
                    "error": None,
                    "updated_at": _now(),
                }
            },
        )
        return res.modified_count == 1

    async def fail(self, job_id: str, error: JobError) -> bool:
        """
        queued|running -> failed
        """
        payload = error.model_dump(mode="json")

        coll = await self._get_collection()
        res = await coll.update_one(
            {"_id": job_id, "status": {"$in": [JobStatusEnum.queued.value, JobStatusEnum.running.value]}},
            {"$set": {"status": JobStatusEnum.failed.value, "error": payload, "updated_at": _now()}},
        )
        return res.modified_count == 1

    # ------------- indexes (optional helper) -------------

    @staticmethod
    async def ensure_indexes(db) -> None:
        jobs = db.get_collection("jobs")
        # idempotency unique (partial)
        await jobs.create_index(
            [("idempotency_key", 1), ("task_hash", 1)],
            name="uniq_idem_task",
            unique=True,
            partialFilterExpression={"idempotency_key": {"$exists": True, "$type": "string"}},
        )
        await jobs.create_index([("status", 1), ("updated_at", -1)], name="status_updated")
        # TTL only for terminal states
        await jobs.create_index(
            [("updated_at", 1)],
            name="ttl_48h_terminal",
            expireAfterSeconds=172800,
            partialFilterExpression={"status": {"$in": ["succeeded", "failed", "canceled"]}},
        )
