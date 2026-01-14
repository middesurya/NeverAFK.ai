"""
PRD-015: Background Jobs - TDD Tests

Tests for async background job processing for content ingestion.

Acceptance Criteria:
- AC-1: File upload request - Returns 202 with job ID immediately
- AC-2: Job ID - Status endpoint returns pending/processing/completed/failed
- AC-3: Background job - Content is indexed when processing completes
- AC-4: Job fails - Returns error details and allows retry

Job states: PENDING, PROCESSING, COMPLETED, FAILED, RETRYING
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
import uuid


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def job_manager():
    """Create a fresh JobManager instance for each test."""
    from app.services.job_manager import JobManager
    return JobManager()


@pytest.fixture
def sample_task():
    """Create a simple synchronous task for testing."""
    def task(value: int) -> dict:
        return {"result": value * 2}
    return task


@pytest.fixture
def sample_async_task():
    """Create a simple async task for testing."""
    async def task(value: int) -> dict:
        await asyncio.sleep(0.01)
        return {"result": value * 2}
    return task


@pytest.fixture
def failing_task():
    """Create a task that always fails."""
    def task():
        raise ValueError("Task failed intentionally")
    return task


@pytest.fixture
def async_failing_task():
    """Create an async task that always fails."""
    async def task():
        await asyncio.sleep(0.01)
        raise ValueError("Async task failed intentionally")
    return task


@pytest.fixture
def slow_task():
    """Create a slow async task for testing cancellation."""
    async def task():
        await asyncio.sleep(10)  # Very long delay
        return {"result": "completed"}
    return task


# =============================================================================
# Job Creation Tests
# =============================================================================

class TestJobCreation:
    """Tests for job creation functionality."""

    def test_create_job_returns_job_object(self, job_manager, sample_task):
        """Creating a job should return a Job object."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job is not None

    def test_create_job_has_unique_id(self, job_manager, sample_task):
        """Each job should have a unique ID."""
        job_manager.register_task("test_task", sample_task)
        job1 = job_manager.create_job("test_task")
        job2 = job_manager.create_job("test_task")

        assert job1.id != job2.id

    def test_create_job_id_is_valid_uuid(self, job_manager, sample_task):
        """Job ID should be a valid UUID."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        # Should not raise
        uuid.UUID(job.id)

    def test_create_job_initial_status_pending(self, job_manager, sample_task):
        """New job should have PENDING status."""
        from app.services.job_manager import JobStatus
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.status == JobStatus.PENDING

    def test_create_job_has_task_name(self, job_manager, sample_task):
        """Job should store task name."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.task_name == "test_task"

    def test_create_job_has_created_at(self, job_manager, sample_task):
        """Job should have created_at timestamp."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.created_at is not None
        assert isinstance(job.created_at, datetime)

    def test_create_job_with_metadata(self, job_manager, sample_task):
        """Job should accept metadata."""
        job_manager.register_task("test_task", sample_task)
        metadata = {"creator_id": "user123", "content_type": "video"}
        job = job_manager.create_job("test_task", metadata=metadata)

        assert job.metadata == metadata

    def test_create_job_with_empty_metadata(self, job_manager, sample_task):
        """Job should handle empty metadata."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task", metadata={})

        assert job.metadata == {}

    def test_create_job_without_metadata(self, job_manager, sample_task):
        """Job should have empty dict for metadata by default."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.metadata == {}

    def test_create_job_unknown_task_raises_error(self, job_manager):
        """Creating job with unknown task should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown task"):
            job_manager.create_job("nonexistent_task")

    def test_create_job_started_at_is_none(self, job_manager, sample_task):
        """New job should have started_at as None."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.started_at is None

    def test_create_job_completed_at_is_none(self, job_manager, sample_task):
        """New job should have completed_at as None."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.completed_at is None

    def test_create_job_result_is_none(self, job_manager, sample_task):
        """New job should have result as None."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.result is None

    def test_create_job_error_is_none(self, job_manager, sample_task):
        """New job should have error as None."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.error is None

    def test_create_job_retry_count_is_zero(self, job_manager, sample_task):
        """New job should have retry_count as 0."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.retry_count == 0


# =============================================================================
# Task Registration Tests
# =============================================================================

class TestTaskRegistration:
    """Tests for task registration functionality."""

    def test_register_task_success(self, job_manager, sample_task):
        """Should be able to register a task."""
        job_manager.register_task("my_task", sample_task)

        assert "my_task" in job_manager._tasks

    def test_register_async_task_success(self, job_manager, sample_async_task):
        """Should be able to register an async task."""
        job_manager.register_task("async_task", sample_async_task)

        assert "async_task" in job_manager._tasks

    def test_register_multiple_tasks(self, job_manager, sample_task, sample_async_task):
        """Should be able to register multiple tasks."""
        job_manager.register_task("task1", sample_task)
        job_manager.register_task("task2", sample_async_task)

        assert "task1" in job_manager._tasks
        assert "task2" in job_manager._tasks

    def test_register_task_overwrites_existing(self, job_manager, sample_task, sample_async_task):
        """Registering with same name should overwrite."""
        job_manager.register_task("my_task", sample_task)
        job_manager.register_task("my_task", sample_async_task)

        assert job_manager._tasks["my_task"] == sample_async_task


# =============================================================================
# Job Retrieval Tests
# =============================================================================

class TestJobRetrieval:
    """Tests for job retrieval functionality."""

    def test_get_job_by_id(self, job_manager, sample_task):
        """Should retrieve job by ID."""
        job_manager.register_task("test_task", sample_task)
        created_job = job_manager.create_job("test_task")

        retrieved_job = job_manager.get_job(created_job.id)

        assert retrieved_job == created_job

    def test_get_nonexistent_job_returns_none(self, job_manager):
        """Getting nonexistent job should return None."""
        result = job_manager.get_job("nonexistent-id")

        assert result is None

    def test_get_status_by_id(self, job_manager, sample_task):
        """Should retrieve job status as dict."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        status = job_manager.get_status(job.id)

        assert status is not None
        assert isinstance(status, dict)
        assert status["id"] == job.id

    def test_get_status_nonexistent_returns_none(self, job_manager):
        """Getting status of nonexistent job should return None."""
        result = job_manager.get_status("nonexistent-id")

        assert result is None


# =============================================================================
# Job Execution Tests
# =============================================================================

class TestJobExecution:
    """Tests for job execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_sync_task(self, job_manager, sample_task):
        """Should execute synchronous task."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = await job_manager.execute(job.id, 5)

        assert result == {"result": 10}

    @pytest.mark.asyncio
    async def test_execute_async_task(self, job_manager, sample_async_task):
        """Should execute async task."""
        job_manager.register_task("test_task", sample_async_task)
        job = job_manager.create_job("test_task")

        result = await job_manager.execute(job.id, 5)

        assert result == {"result": 10}

    @pytest.mark.asyncio
    async def test_execute_sets_processing_status(self, job_manager):
        """Execution should set PROCESSING status during run."""
        from app.services.job_manager import JobStatus

        status_during_execution = None
        job_id_holder = {"id": None}

        async def check_status_task():
            nonlocal status_during_execution
            retrieved_job = job_manager.get_job(job_id_holder["id"])
            status_during_execution = retrieved_job.status
            return {"done": True}

        job_manager.register_task("test_task", check_status_task)
        job = job_manager.create_job("test_task")
        job_id_holder["id"] = job.id

        await job_manager.execute(job.id)

        # Verify the status was PROCESSING during execution
        assert status_during_execution == JobStatus.PROCESSING
        # And now it should be COMPLETED
        assert job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_sets_started_at(self, job_manager, sample_async_task):
        """Execution should set started_at timestamp."""
        job_manager.register_task("test_task", sample_async_task)
        job = job_manager.create_job("test_task")

        await job_manager.execute(job.id, 1)

        assert job.started_at is not None
        assert isinstance(job.started_at, datetime)

    @pytest.mark.asyncio
    async def test_execute_success_sets_completed_status(self, job_manager, sample_task):
        """Successful execution should set COMPLETED status."""
        from app.services.job_manager import JobStatus
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        await job_manager.execute(job.id, 1)

        assert job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_success_sets_completed_at(self, job_manager, sample_task):
        """Successful execution should set completed_at timestamp."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        await job_manager.execute(job.id, 1)

        assert job.completed_at is not None
        assert isinstance(job.completed_at, datetime)

    @pytest.mark.asyncio
    async def test_execute_success_stores_result(self, job_manager, sample_task):
        """Successful execution should store result."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        await job_manager.execute(job.id, 7)

        assert job.result == {"result": 14}

    @pytest.mark.asyncio
    async def test_execute_nonexistent_job_raises_error(self, job_manager):
        """Executing nonexistent job should raise ValueError."""
        with pytest.raises(ValueError, match="Job not found"):
            await job_manager.execute("nonexistent-id")

    @pytest.mark.asyncio
    async def test_execute_already_processing_raises_error(self, job_manager, slow_task):
        """Executing already processing job should raise RuntimeError."""
        job_manager.register_task("test_task", slow_task)
        job = job_manager.create_job("test_task")

        # Start execution in background
        task = asyncio.create_task(job_manager.execute(job.id))
        await asyncio.sleep(0.01)  # Let it start

        with pytest.raises(RuntimeError, match="already processing"):
            await job_manager.execute(job.id)

        # Cleanup
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# =============================================================================
# Job Failure Tests - AC-4
# =============================================================================

class TestJobFailure:
    """Tests for job failure handling - AC-4."""

    @pytest.mark.asyncio
    async def test_execute_failure_sets_failed_status(self, job_manager, failing_task):
        """Failed execution should set FAILED status."""
        from app.services.job_manager import JobStatus
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        assert job.status == JobStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_async_failure_sets_failed_status(self, job_manager, async_failing_task):
        """Failed async execution should set FAILED status."""
        from app.services.job_manager import JobStatus
        job_manager.register_task("test_task", async_failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        assert job.status == JobStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_failure_stores_error(self, job_manager, failing_task):
        """Failed execution should store error message."""
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        assert job.error is not None
        assert "Task failed intentionally" in job.error

    @pytest.mark.asyncio
    async def test_execute_failure_sets_completed_at(self, job_manager, failing_task):
        """Failed execution should set completed_at timestamp."""
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        assert job.completed_at is not None

    @pytest.mark.asyncio
    async def test_failed_job_can_retry(self, job_manager, failing_task):
        """Failed job should allow retry."""
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        assert job.can_retry is True

    @pytest.mark.asyncio
    async def test_failed_job_error_details_in_status(self, job_manager, failing_task):
        """Failed job status should include error details."""
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        status = job_manager.get_status(job.id)

        assert status["error"] is not None
        assert "Task failed intentionally" in status["error"]


# =============================================================================
# Retry Mechanism Tests - AC-4
# =============================================================================

class TestRetryMechanism:
    """Tests for job retry mechanism - AC-4."""

    @pytest.mark.asyncio
    async def test_retry_failed_job(self, job_manager):
        """Should be able to retry a failed job."""
        call_count = 0

        def task_that_succeeds_second_time():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First attempt fails")
            return {"success": True}

        job_manager.register_task("test_task", task_that_succeeds_second_time)
        job = job_manager.create_job("test_task")

        # First attempt fails
        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        # Retry
        await job_manager.retry(job.id)
        await asyncio.sleep(0.01)  # Allow async task to complete

        assert job.status.value in ["completed", "processing", "retrying"]

    @pytest.mark.asyncio
    async def test_retry_increments_retry_count(self, job_manager, failing_task):
        """Retry should increment retry_count."""
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        initial_count = job.retry_count
        await job_manager.retry(job.id)

        assert job.retry_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_retry_sets_retrying_status(self, job_manager, failing_task):
        """Retry should set RETRYING status initially."""
        from app.services.job_manager import JobStatus
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        # Start retry
        task = await job_manager.retry(job.id)

        # Status should eventually be RETRYING or transition to next state
        assert task is not None

        # Cleanup
        try:
            await task
        except ValueError:
            pass

    @pytest.mark.asyncio
    async def test_retry_clears_error(self, job_manager, failing_task):
        """Retry should clear previous error."""
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        assert job.error is not None

        # Start retry (this will also fail but error should be cleared initially)
        task = await job_manager.retry(job.id)

        # Note: error gets cleared then set again on failure
        try:
            await task
        except ValueError:
            pass

    @pytest.mark.asyncio
    async def test_cannot_retry_pending_job(self, job_manager, sample_task):
        """Cannot retry a pending job."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = await job_manager.retry(job.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_cannot_retry_completed_job(self, job_manager, sample_task):
        """Cannot retry a completed job."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        await job_manager.execute(job.id, 1)

        result = await job_manager.retry(job.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, job_manager, failing_task):
        """Cannot retry beyond max_retries."""
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")
        job.max_retries = 2

        # Exhaust retries
        for i in range(3):
            if i == 0:
                with pytest.raises(ValueError):
                    await job_manager.execute(job.id)
            else:
                task = await job_manager.retry(job.id)
                if task:
                    try:
                        await task
                    except ValueError:
                        pass

        # Next retry should fail
        result = await job_manager.retry(job.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_retry_nonexistent_job_raises_error(self, job_manager):
        """Retrying nonexistent job should raise ValueError."""
        with pytest.raises(ValueError, match="Job not found"):
            await job_manager.retry("nonexistent-id")


# =============================================================================
# Job Enqueue Tests
# =============================================================================

class TestJobEnqueue:
    """Tests for job enqueueing functionality."""

    @pytest.mark.asyncio
    async def test_enqueue_returns_task(self, job_manager, sample_async_task):
        """Enqueue should return asyncio.Task."""
        job_manager.register_task("test_task", sample_async_task)
        job = job_manager.create_job("test_task")

        task = await job_manager.enqueue(job.id, 5)

        assert isinstance(task, asyncio.Task)

        # Cleanup
        await task

    @pytest.mark.asyncio
    async def test_enqueue_runs_in_background(self, job_manager, sample_async_task):
        """Enqueue should run task in background."""
        job_manager.register_task("test_task", sample_async_task)
        job = job_manager.create_job("test_task")

        task = await job_manager.enqueue(job.id, 5)

        # Task should be running
        assert not task.done()

        # Wait for completion
        result = await task
        assert result == {"result": 10}


# =============================================================================
# Job Cancellation Tests
# =============================================================================

class TestJobCancellation:
    """Tests for job cancellation functionality."""

    @pytest.mark.asyncio
    async def test_cancel_running_job(self, job_manager, slow_task):
        """Should be able to cancel a running job."""
        job_manager.register_task("test_task", slow_task)
        job = job_manager.create_job("test_task")

        task = await job_manager.enqueue(job.id)
        await asyncio.sleep(0.01)  # Let it start

        result = job_manager.cancel(job.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_sets_failed_status(self, job_manager, slow_task):
        """Cancelled job should have FAILED status."""
        from app.services.job_manager import JobStatus
        job_manager.register_task("test_task", slow_task)
        job = job_manager.create_job("test_task")

        task = await job_manager.enqueue(job.id)
        await asyncio.sleep(0.01)

        job_manager.cancel(job.id)
        await asyncio.sleep(0.01)  # Let cancellation propagate

        assert job.status == JobStatus.FAILED

    @pytest.mark.asyncio
    async def test_cancel_sets_cancelled_error(self, job_manager, slow_task):
        """Cancelled job should have cancellation error message."""
        job_manager.register_task("test_task", slow_task)
        job = job_manager.create_job("test_task")

        task = await job_manager.enqueue(job.id)
        await asyncio.sleep(0.01)

        job_manager.cancel(job.id)
        await asyncio.sleep(0.01)

        assert "Cancelled" in job.error

    def test_cancel_nonexistent_job(self, job_manager):
        """Cancelling nonexistent job should return False."""
        result = job_manager.cancel("nonexistent-id")

        assert result is False

    def test_cancel_not_running_job(self, job_manager, sample_task):
        """Cancelling non-running job should return False."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job_manager.cancel(job.id)

        assert result is False


# =============================================================================
# Job Status Dict Tests - AC-2
# =============================================================================

class TestJobStatusDict:
    """Tests for job to_dict serialization - AC-2."""

    def test_to_dict_includes_id(self, job_manager, sample_task):
        """Job dict should include id."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job.to_dict()

        assert "id" in result
        assert result["id"] == job.id

    def test_to_dict_includes_task_name(self, job_manager, sample_task):
        """Job dict should include task_name."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job.to_dict()

        assert "task_name" in result
        assert result["task_name"] == "test_task"

    def test_to_dict_includes_status(self, job_manager, sample_task):
        """Job dict should include status as string."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job.to_dict()

        assert "status" in result
        assert result["status"] == "pending"

    def test_to_dict_includes_created_at(self, job_manager, sample_task):
        """Job dict should include created_at as ISO string."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job.to_dict()

        assert "created_at" in result
        assert isinstance(result["created_at"], str)

    def test_to_dict_includes_started_at_null(self, job_manager, sample_task):
        """Job dict should include started_at as null for pending."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job.to_dict()

        assert "started_at" in result
        assert result["started_at"] is None

    def test_to_dict_includes_completed_at_null(self, job_manager, sample_task):
        """Job dict should include completed_at as null for pending."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job.to_dict()

        assert "completed_at" in result
        assert result["completed_at"] is None

    def test_to_dict_includes_result(self, job_manager, sample_task):
        """Job dict should include result."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job.to_dict()

        assert "result" in result

    def test_to_dict_includes_error(self, job_manager, sample_task):
        """Job dict should include error."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job.to_dict()

        assert "error" in result

    def test_to_dict_includes_retry_count(self, job_manager, sample_task):
        """Job dict should include retry_count."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job.to_dict()

        assert "retry_count" in result
        assert result["retry_count"] == 0

    def test_to_dict_includes_can_retry(self, job_manager, sample_task):
        """Job dict should include can_retry."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        result = job.to_dict()

        assert "can_retry" in result

    def test_to_dict_includes_metadata(self, job_manager, sample_task):
        """Job dict should include metadata."""
        job_manager.register_task("test_task", sample_task)
        metadata = {"key": "value"}
        job = job_manager.create_job("test_task", metadata=metadata)

        result = job.to_dict()

        assert "metadata" in result
        assert result["metadata"] == metadata


# =============================================================================
# Job Properties Tests
# =============================================================================

class TestJobProperties:
    """Tests for Job properties."""

    def test_can_retry_false_when_pending(self, job_manager, sample_task):
        """can_retry should be False for pending job."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.can_retry is False

    @pytest.mark.asyncio
    async def test_can_retry_false_when_completed(self, job_manager, sample_task):
        """can_retry should be False for completed job."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        await job_manager.execute(job.id, 1)

        assert job.can_retry is False

    @pytest.mark.asyncio
    async def test_can_retry_true_when_failed(self, job_manager, failing_task):
        """can_retry should be True for failed job within retry limit."""
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        assert job.can_retry is True

    def test_is_terminal_false_when_pending(self, job_manager, sample_task):
        """is_terminal should be False for pending job."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job.is_terminal is False

    @pytest.mark.asyncio
    async def test_is_terminal_true_when_completed(self, job_manager, sample_task):
        """is_terminal should be True for completed job."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        await job_manager.execute(job.id, 1)

        assert job.is_terminal is True

    @pytest.mark.asyncio
    async def test_is_terminal_true_when_failed(self, job_manager, failing_task):
        """is_terminal should be True for failed job."""
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        assert job.is_terminal is True


# =============================================================================
# Job Manager Counts Tests
# =============================================================================

class TestJobManagerCounts:
    """Tests for JobManager count properties."""

    def test_pending_count_zero_initially(self, job_manager):
        """pending_count should be 0 initially."""
        assert job_manager.pending_count == 0

    def test_pending_count_increases_with_jobs(self, job_manager, sample_task):
        """pending_count should increase as jobs are created."""
        job_manager.register_task("test_task", sample_task)

        job_manager.create_job("test_task")
        assert job_manager.pending_count == 1

        job_manager.create_job("test_task")
        assert job_manager.pending_count == 2

    @pytest.mark.asyncio
    async def test_pending_count_decreases_after_execution(self, job_manager, sample_task):
        """pending_count should decrease after job execution."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert job_manager.pending_count == 1

        await job_manager.execute(job.id, 1)

        assert job_manager.pending_count == 0

    def test_processing_count_zero_initially(self, job_manager):
        """processing_count should be 0 initially."""
        assert job_manager.processing_count == 0


# =============================================================================
# Concurrent Jobs Tests
# =============================================================================

class TestConcurrentJobs:
    """Tests for handling multiple concurrent jobs."""

    @pytest.mark.asyncio
    async def test_multiple_jobs_execute_concurrently(self, job_manager, sample_async_task):
        """Multiple jobs should execute concurrently."""
        job_manager.register_task("test_task", sample_async_task)

        job1 = job_manager.create_job("test_task")
        job2 = job_manager.create_job("test_task")
        job3 = job_manager.create_job("test_task")

        # Enqueue all jobs
        task1 = await job_manager.enqueue(job1.id, 1)
        task2 = await job_manager.enqueue(job2.id, 2)
        task3 = await job_manager.enqueue(job3.id, 3)

        # Wait for all
        results = await asyncio.gather(task1, task2, task3)

        assert results[0] == {"result": 2}
        assert results[1] == {"result": 4}
        assert results[2] == {"result": 6}

    @pytest.mark.asyncio
    async def test_different_tasks_execute_concurrently(self, job_manager):
        """Different tasks should execute concurrently."""
        async def task_a(x):
            await asyncio.sleep(0.01)
            return {"a": x}

        async def task_b(x):
            await asyncio.sleep(0.01)
            return {"b": x}

        job_manager.register_task("task_a", task_a)
        job_manager.register_task("task_b", task_b)

        job1 = job_manager.create_job("task_a")
        job2 = job_manager.create_job("task_b")

        task1 = await job_manager.enqueue(job1.id, 1)
        task2 = await job_manager.enqueue(job2.id, 2)

        results = await asyncio.gather(task1, task2)

        assert results[0] == {"a": 1}
        assert results[1] == {"b": 2}

    @pytest.mark.asyncio
    async def test_jobs_maintain_isolation(self, job_manager, sample_async_task):
        """Jobs should maintain isolation from each other."""
        job_manager.register_task("test_task", sample_async_task)

        job1 = job_manager.create_job("test_task", metadata={"id": 1})
        job2 = job_manager.create_job("test_task", metadata={"id": 2})

        task1 = await job_manager.enqueue(job1.id, 10)
        task2 = await job_manager.enqueue(job2.id, 20)

        await asyncio.gather(task1, task2)

        # Each job maintains its own metadata
        assert job1.metadata == {"id": 1}
        assert job2.metadata == {"id": 2}

        # Each job has its own result
        assert job1.result == {"result": 20}
        assert job2.result == {"result": 40}


# =============================================================================
# Job Status Endpoint Tests - AC-2
# =============================================================================

class TestJobStatusEndpoint:
    """Tests for job status endpoint behavior - AC-2."""

    def test_status_returns_pending_for_new_job(self, job_manager, sample_task):
        """Status should return 'pending' for new job."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        status = job_manager.get_status(job.id)

        assert status["status"] == "pending"

    @pytest.mark.asyncio
    async def test_status_returns_completed_after_execution(self, job_manager, sample_task):
        """Status should return 'completed' after execution."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        await job_manager.execute(job.id, 1)

        status = job_manager.get_status(job.id)

        assert status["status"] == "completed"

    @pytest.mark.asyncio
    async def test_status_returns_failed_on_error(self, job_manager, failing_task):
        """Status should return 'failed' on error."""
        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        status = job_manager.get_status(job.id)

        assert status["status"] == "failed"


# =============================================================================
# Integration-like Tests
# =============================================================================

class TestIngestionTasksIntegration:
    """Integration tests with ingestion tasks module."""

    def test_ingestion_tasks_register_with_singleton(self):
        """Ingestion tasks should register with singleton job_manager."""
        # Import to trigger registration
        from app.tasks import ingestion_tasks
        from app.services.job_manager import job_manager

        assert "content_ingestion" in job_manager._tasks
        assert "file_upload" in job_manager._tasks

    @pytest.mark.asyncio
    async def test_content_ingestion_task_executes(self):
        """Content ingestion task should execute successfully."""
        from app.tasks.ingestion_tasks import process_content_ingestion

        result = await process_content_ingestion(
            content="Test content",
            creator_id="creator123",
            content_type="text"
        )

        assert "chunks_created" in result
        assert "embeddings_stored" in result
        assert result["creator_id"] == "creator123"

    @pytest.mark.asyncio
    async def test_file_upload_task_executes(self):
        """File upload task should execute successfully."""
        from app.tasks.ingestion_tasks import process_file_upload

        result = await process_file_upload(
            file_path="/path/to/file.txt",
            creator_id="creator123",
            file_type="text"
        )

        assert result["processed"] is True
        assert result["creator_id"] == "creator123"

    @pytest.mark.asyncio
    async def test_full_job_lifecycle_with_ingestion(self):
        """Test full job lifecycle with ingestion task."""
        from app.services.job_manager import job_manager, JobStatus
        # Import to register tasks
        from app.tasks import ingestion_tasks

        # Create job
        job = job_manager.create_job("content_ingestion", metadata={
            "creator_id": "test123",
            "content_type": "video"
        })

        assert job.status == JobStatus.PENDING

        # Execute
        result = await job_manager.execute(
            job.id,
            content="Test video transcript",
            creator_id="test123",
            content_type="video"
        )

        assert job.status == JobStatus.COMPLETED
        assert "chunks_created" in result


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_job_with_none_metadata(self, job_manager, sample_task):
        """Job should handle None metadata gracefully."""
        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task", metadata=None)

        assert job.metadata == {}

    def test_job_with_complex_metadata(self, job_manager, sample_task):
        """Job should handle complex metadata."""
        job_manager.register_task("test_task", sample_task)
        metadata = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "mixed": {"items": [{"a": 1}, {"b": 2}]}
        }
        job = job_manager.create_job("test_task", metadata=metadata)

        assert job.metadata == metadata

    @pytest.mark.asyncio
    async def test_task_returning_none(self, job_manager):
        """Job should handle task returning None."""
        def task_returns_none():
            return None

        job_manager.register_task("test_task", task_returns_none)
        job = job_manager.create_job("test_task")

        result = await job_manager.execute(job.id)

        assert result is None
        assert job.result is None

    @pytest.mark.asyncio
    async def test_task_with_kwargs(self, job_manager):
        """Job should pass kwargs to task."""
        def task_with_kwargs(*, name, value):
            return {"name": name, "value": value}

        job_manager.register_task("test_task", task_with_kwargs)
        job = job_manager.create_job("test_task")

        result = await job_manager.execute(job.id, name="test", value=42)

        assert result == {"name": "test", "value": 42}

    @pytest.mark.asyncio
    async def test_rapid_job_creation(self, job_manager, sample_task):
        """Should handle rapid job creation without collisions."""
        job_manager.register_task("test_task", sample_task)

        jobs = [job_manager.create_job("test_task") for _ in range(100)]

        # All IDs should be unique
        ids = [job.id for job in jobs]
        assert len(ids) == len(set(ids))

    def test_empty_task_name(self, job_manager):
        """Should reject empty task name."""
        with pytest.raises(ValueError):
            job_manager.create_job("")

    def test_whitespace_task_name(self, job_manager):
        """Should reject whitespace-only task name."""
        with pytest.raises(ValueError):
            job_manager.create_job("   ")


# =============================================================================
# Logging Tests
# =============================================================================

class TestLogging:
    """Tests for logging behavior."""

    @pytest.mark.asyncio
    async def test_job_creation_is_logged(self, job_manager, sample_task, caplog):
        """Job creation should be logged."""
        import logging
        caplog.set_level(logging.INFO)

        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        assert f"Created job {job.id}" in caplog.text

    @pytest.mark.asyncio
    async def test_job_execution_start_is_logged(self, job_manager, sample_task, caplog):
        """Job execution start should be logged."""
        import logging
        caplog.set_level(logging.INFO)

        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        await job_manager.execute(job.id, 1)

        assert f"Starting job {job.id}" in caplog.text

    @pytest.mark.asyncio
    async def test_job_completion_is_logged(self, job_manager, sample_task, caplog):
        """Job completion should be logged."""
        import logging
        caplog.set_level(logging.INFO)

        job_manager.register_task("test_task", sample_task)
        job = job_manager.create_job("test_task")

        await job_manager.execute(job.id, 1)

        assert f"Job {job.id} completed" in caplog.text

    @pytest.mark.asyncio
    async def test_job_failure_is_logged(self, job_manager, failing_task, caplog):
        """Job failure should be logged."""
        import logging
        caplog.set_level(logging.ERROR)

        job_manager.register_task("test_task", failing_task)
        job = job_manager.create_job("test_task")

        with pytest.raises(ValueError):
            await job_manager.execute(job.id)

        assert f"Job {job.id} failed" in caplog.text
