from typing import Optional

from app.core.config import config
from app.workers.tasks import run_agent_task


class Producer:
    """Celery producer: apply_async is called directly (sync)."""

    def __init__(self, queue_name: str = config.QUEUE_NAME) -> None:
        self.queue_name = queue_name

    def enqueue_execute(self, *, job_id: str, request_id: str, owner_user_id: Optional[str] = None) -> None:
        headers = {
            "request_id": request_id,
            "job_id": job_id,
            "owner_user_id": owner_user_id,
        }
        run_agent_task.apply_async(
            kwargs={"job_id": job_id, "request_id": request_id},
            queue=self.queue_name,
            headers=headers,
        )
