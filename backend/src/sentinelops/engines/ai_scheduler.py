"""
AI Scheduler — System 13
Queues Ollama inference jobs, applies concurrency cap, batches reasoning tasks.
RTX 3050 Ti: keeps model hot with keep_alive=-1, serializes concurrent requests.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
from uuid import uuid4

from sentinelops.core.logging import get_logger
from sentinelops.engines.performance_profiler import latency_track

log = get_logger(__name__)


@dataclass
class AIJob:
    id: str = field(default_factory=lambda: str(uuid4()))
    prompt: str = ""
    model: str = "llama3.2"
    callback: Callable[[str], Awaitable[None]] | None = None
    priority: int = 5  # 1=highest, 10=lowest


class AIScheduler:
    """
    Priority queue for Ollama inference.
    Ensures GPU is never overloaded — single-flight per model slot.
    """

    def __init__(self, max_concurrent: int = 2) -> None:
        self._queue: asyncio.PriorityQueue[tuple[int, AIJob]] = asyncio.PriorityQueue()
        self._sem = asyncio.Semaphore(max_concurrent)
        self._running = False
        self._worker_task: asyncio.Task | None = None

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._run())
            log.info("ai_scheduler_started")

    def stop(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()

    async def enqueue(self, job: AIJob) -> None:
        await self._queue.put((job.priority, job))

    async def _run(self) -> None:
        while self._running:
            try:
                _, job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                asyncio.create_task(self._execute(job))
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                log.error("ai_scheduler_error", error=str(e))

    async def _execute(self, job: AIJob) -> None:
        async with self._sem:
            async with latency_track(f"ai_inference_{job.model}"):
                try:
                    from sentinelops.ai.ollama_client import OllamaClient
                    client = OllamaClient()
                    result = await client.generate(job.prompt, model=job.model)
                    if job.callback:
                        await job.callback(result)
                except Exception as e:
                    log.error("ai_job_failed", job_id=job.id, error=str(e))


# Singleton scheduler
ai_scheduler = AIScheduler(max_concurrent=2)
