from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.api import ExecuteRequest
from app.schemas.auth import ActorSchema
from app.services.jobs_orchestrator import JobsOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_idempotency_short_circuit():
    jobs = MagicMock()
    logs = MagicMock()
    producer = MagicMock()

    # idempotent: eski job bulundu → kısa devre
    jobs.get_by_idempotency = AsyncMock(return_value=SimpleNamespace(job_id="j_old", request_id="r_old"))

    orch = JobsOrchestrator(jobs_repo=jobs, logs_repo=logs, producer=producer)
    payload = ExecuteRequest(task="abc", mode="async", webhook_url=None)
    actor = ActorSchema(user_id=1, email="u@e", is_active=True)

    accepted, location = await orch.create_and_enqueue(payload, actor, http_request_id="rid", idempotency_key="idem1")
    assert accepted.job_id == "j_old"
    assert location.endswith("/j_old")
    jobs.create_job.assert_not_called()
    producer.enqueue_execute.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_new_job_enqueues():
    jobs = MagicMock()
    logs = MagicMock()
    producer = MagicMock()

    jobs.get_by_idempotency = AsyncMock(return_value=None)
    jobs.create_job = AsyncMock()
    logs.push = AsyncMock()

    # enqueue_execute SENKRON -> MagicMock kullan
    producer.enqueue_execute = MagicMock()

    orch = JobsOrchestrator(jobs_repo=jobs, logs_repo=logs, producer=producer)
    payload = ExecuteRequest(task="do something", mode="async", webhook_url=None)
    actor = ActorSchema(user_id=123, email="u@e", is_active=True)

    accepted, location = await orch.create_and_enqueue(payload, actor, http_request_id="rid", idempotency_key="idem2")

    assert accepted.job_id.startswith("j_")
    assert accepted.status == "queued"
    assert "/api/v1/jobs/" in location

    jobs.create_job.assert_awaited_once()
    logs.push.assert_awaited()  # en az bir kere
    producer.enqueue_execute.assert_called_once()

    # Argümanları da doğrulayalım:
    _, kwargs = producer.enqueue_execute.call_args
    assert kwargs["job_id"] == accepted.job_id
    assert kwargs["request_id"] == accepted.request_id
    assert kwargs["owner_user_id"] == str(actor.user_id)
