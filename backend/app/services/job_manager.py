"""
PRD-015: Background Jobs - Job Manager Service

Manages background job lifecycle for async content processing.

Job states:
- PENDING: Job created but not started
- PROCESSING: Job currently executing
- COMPLETED: Job finished successfully
- FAILED: Job failed with error
- RETRYING: Job being retried after failure
"""

import uuid
import asyncio
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Enumeration of possible job states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Job:
    """
    Represents a background job.

    Attributes:
        id: Unique job identifier (UUID)
        task_name: Name of the registered task to execute
        status: Current job status
        created_at: Timestamp when job was created
        started_at: Timestamp when job started processing
        completed_at: Timestamp when job finished (success or failure)
        result: Result data from successful execution
        error: Error message from failed execution
        retry_count: Number of retry attempts made
        max_retries: Maximum allowed retry attempts
        metadata: Additional job metadata (e.g., creator_id, content_type)
    """
    id: str
    task_name: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Convert job to dictionary representation.

        Returns:
            Dictionary with all job attributes serialized.
        """
        return {
            "id": self.id,
            "task_name": self.task_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "can_retry": self.can_retry,
            "metadata": self.metadata,
        }

    @property
    def can_retry(self) -> bool:
        """
        Check if job can be retried.

        Returns:
            True if job is failed and hasn't exceeded max retries.
        """
        return self.status == JobStatus.FAILED and self.retry_count < self.max_retries

    @property
    def is_terminal(self) -> bool:
        """
        Check if job is in a terminal state.

        Returns:
            True if job is completed or failed.
        """
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)


class JobManager:
    """
    Manages background job lifecycle.

    Provides methods to:
    - Register task functions
    - Create jobs for registered tasks
    - Execute jobs synchronously or asynchronously
    - Retry failed jobs
    - Cancel running jobs
    - Query job status
    """

    def __init__(self):
        """Initialize job manager with empty job and task stores."""
        self._jobs: dict[str, Job] = {}
        self._tasks: dict[str, Callable] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}

    def register_task(self, name: str, func: Callable) -> None:
        """
        Register a task function.

        Args:
            name: Unique name for the task
            func: Callable (sync or async) to execute
        """
        self._tasks[name] = func

    def create_job(self, task_name: str, metadata: dict = None) -> Job:
        """
        Create a new job for a registered task.

        Args:
            task_name: Name of registered task
            metadata: Optional metadata for the job

        Returns:
            Newly created Job instance

        Raises:
            ValueError: If task_name is not registered or invalid
        """
        # Validate task name
        if not task_name or not task_name.strip():
            raise ValueError(f"Unknown task: {task_name}")

        if task_name not in self._tasks:
            raise ValueError(f"Unknown task: {task_name}")

        job = Job(
            id=str(uuid.uuid4()),
            task_name=task_name,
            metadata=metadata if metadata is not None else {}
        )
        self._jobs[job.id] = job
        logger.info(f"Created job {job.id} for task {task_name}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job instance or None if not found
        """
        return self._jobs.get(job_id)

    def get_status(self, job_id: str) -> Optional[dict]:
        """
        Get job status as dictionary.

        Args:
            job_id: Job identifier

        Returns:
            Job status dict or None if not found
        """
        job = self.get_job(job_id)
        return job.to_dict() if job else None

    async def execute(self, job_id: str, *args, **kwargs) -> Any:
        """
        Execute job asynchronously.

        Args:
            job_id: Job identifier
            *args: Positional arguments for task
            **kwargs: Keyword arguments for task

        Returns:
            Task result

        Raises:
            ValueError: If job not found or task not registered
            RuntimeError: If job is already processing
        """
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status == JobStatus.PROCESSING:
            raise RuntimeError(f"Job {job_id} is already processing")

        task_func = self._tasks.get(job.task_name)
        if not task_func:
            raise ValueError(f"Task not registered: {job.task_name}")

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        logger.info(f"Starting job {job_id}")

        try:
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*args, **kwargs)
            else:
                result = task_func(*args, **kwargs)

            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            logger.info(f"Job {job_id} completed successfully")
            return result
        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error = str(e)
            logger.error(f"Job {job_id} failed: {e}")
            raise

    async def enqueue(self, job_id: str, *args, **kwargs) -> asyncio.Task:
        """
        Enqueue job for background execution.

        Args:
            job_id: Job identifier
            *args: Positional arguments for task
            **kwargs: Keyword arguments for task

        Returns:
            asyncio.Task for the background execution
        """
        task = asyncio.create_task(self.execute(job_id, *args, **kwargs))
        self._running_tasks[job_id] = task
        return task

    async def retry(self, job_id: str, *args, **kwargs) -> Optional[asyncio.Task]:
        """
        Retry a failed job.

        Args:
            job_id: Job identifier
            *args: Positional arguments for task
            **kwargs: Keyword arguments for task

        Returns:
            asyncio.Task if retry started, None if not retryable

        Raises:
            ValueError: If job not found
        """
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if not job.can_retry:
            return None

        job.retry_count += 1
        job.status = JobStatus.RETRYING
        job.error = None
        logger.info(f"Retrying job {job_id} (attempt {job.retry_count})")

        return await self.enqueue(job_id, *args, **kwargs)

    def cancel(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job identifier

        Returns:
            True if job was cancelled, False otherwise
        """
        if job_id in self._running_tasks:
            task = self._running_tasks[job_id]
            if not task.done():
                task.cancel()
                job = self.get_job(job_id)
                if job:
                    job.status = JobStatus.FAILED
                    job.error = "Cancelled by user"
                return True
        return False

    @property
    def pending_count(self) -> int:
        """
        Get count of pending jobs.

        Returns:
            Number of jobs in PENDING state
        """
        return sum(1 for j in self._jobs.values() if j.status == JobStatus.PENDING)

    @property
    def processing_count(self) -> int:
        """
        Get count of processing jobs.

        Returns:
            Number of jobs in PROCESSING state
        """
        return sum(1 for j in self._jobs.values() if j.status == JobStatus.PROCESSING)


# Singleton instance for application-wide job management
job_manager = JobManager()
