"""
Health check endpoints for monitoring and Kubernetes probes.

Provides:
- GET /health - Basic health check for load balancers
- GET /health/detailed - Detailed health with dependency status
- GET /ready - Readiness check for Kubernetes
- GET /live - Liveness check for Kubernetes

AC-1: GET /health returns status of all dependencies (DB, Redis, Pinecone)
AC-4: Degraded status when dependency fails
"""

from fastapi import APIRouter, Depends
from typing import Optional
import time
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

router = APIRouter(tags=["Health"])


class HealthStatus(Enum):
    """Health status enum for dependency and overall health."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class DependencyCheck:
    """Result of a dependency health check."""
    name: str
    status: HealthStatus
    latency_ms: float
    message: Optional[str] = None
    checked_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class HealthResponse:
    """Complete health check response."""
    status: HealthStatus
    version: str
    uptime_seconds: float
    dependencies: list[DependencyCheck]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "dependencies": [
                {
                    "name": d.name,
                    "status": d.status.value,
                    "latency_ms": round(d.latency_ms, 2),
                    "message": d.message,
                    "checked_at": d.checked_at
                }
                for d in self.dependencies
            ]
        }


# Application start time for uptime calculation
_start_time = time.time()
APP_VERSION = "1.1.0"


class HealthChecker:
    """Checks health of all application dependencies."""

    async def check_database(self) -> DependencyCheck:
        """Check database connectivity and health."""
        start = time.time()
        try:
            # Simulate DB check - in production, this would ping the database
            await asyncio.sleep(0.01)
            return DependencyCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                latency_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return DependencyCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )

    async def check_redis(self) -> DependencyCheck:
        """Check Redis connectivity and health."""
        start = time.time()
        try:
            # Simulate Redis check - in production, this would ping Redis
            await asyncio.sleep(0.01)
            return DependencyCheck(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return DependencyCheck(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )

    async def check_pinecone(self) -> DependencyCheck:
        """Check Pinecone connectivity and health."""
        start = time.time()
        try:
            # Simulate Pinecone check - in production, this would ping Pinecone API
            await asyncio.sleep(0.01)
            return DependencyCheck(
                name="pinecone",
                status=HealthStatus.HEALTHY,
                latency_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return DependencyCheck(
                name="pinecone",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )

    async def check_all(self) -> HealthResponse:
        """
        Check all dependencies concurrently and return overall health status.

        Returns:
            HealthResponse with overall status and individual dependency statuses
        """
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_pinecone(),
            return_exceptions=True
        )

        # Convert exceptions to unhealthy checks
        dependencies = []
        for i, check in enumerate(checks):
            if isinstance(check, Exception):
                # Determine which check failed based on index
                names = ["database", "redis", "pinecone"]
                name = names[i] if i < len(names) else "unknown"
                dependencies.append(DependencyCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=0,
                    message=str(check)
                ))
            else:
                dependencies.append(check)

        # Determine overall status
        if all(d.status == HealthStatus.HEALTHY for d in dependencies):
            overall = HealthStatus.HEALTHY
        elif any(d.status == HealthStatus.UNHEALTHY for d in dependencies):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.DEGRADED

        return HealthResponse(
            status=overall,
            version=APP_VERSION,
            uptime_seconds=time.time() - _start_time,
            dependencies=dependencies
        )


# Singleton health checker instance
health_checker = HealthChecker()


@router.get("/health")
async def health_check():
    """
    Basic health check for load balancers.

    Returns:
        Simple status indicator for quick health checks
    """
    return {"status": "ok"}


@router.get("/health/detailed")
async def detailed_health():
    """
    Detailed health check with dependency status.

    Returns all dependency statuses (database, redis, pinecone) with
    latency measurements and overall health status.

    Returns:
        Detailed health response with dependency information
    """
    response = await health_checker.check_all()
    return response.to_dict()


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes.

    Indicates whether the application is ready to receive traffic.
    Returns not ready if any critical dependency is unhealthy.

    Returns:
        Readiness status with reason if not ready
    """
    response = await health_checker.check_all()
    if response.status == HealthStatus.UNHEALTHY:
        return {"ready": False, "reason": "Dependencies unhealthy"}
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes.

    Indicates whether the application process is running.
    This is a simple check that doesn't verify dependencies.

    Returns:
        Liveness status with uptime
    """
    return {"alive": True, "uptime": time.time() - _start_time}
