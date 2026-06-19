"""In-memory job store. Wiped on process restart — that's intentional.

The CSV export is the persistence layer. Operators run a batch, export,
move on.
"""
from __future__ import annotations

import time
import uuid
from collections import OrderedDict
from typing import Literal

from pydantic import BaseModel, Field

from app.config import settings

JobKind = Literal["maps", "website", "email", "facebook", "all", "website_leads"]
JobStatus = Literal["pending", "running", "done", "failed"]
LeadStatus = Literal["pending", "running", "done", "failed", "partial"]


class EmailVerdict(BaseModel):
    email: str
    valid: bool
    reason: str = ""


class Lead(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_url: str
    business_name: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    emails: list[str] = Field(default_factory=list)
    facebook: str | None = None
    status: LeadStatus = "pending"
    error: str | None = None
    elapsed_ms: int | None = None

    # ---- AI verification ---------------------------------------------------
    email_verdicts: list[EmailVerdict] = Field(default_factory=list)
    name_matches: bool | None = None
    ai_note: str | None = None
    ai_checked: bool = False


class Job(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    kind: JobKind
    status: JobStatus = "pending"
    total: int = 0
    done: int = 0
    failed: int = 0
    leads: list[Lead] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    finished_at: float | None = None
    error: str | None = None

    def progress(self) -> float:
        return 0.0 if self.total == 0 else (self.done + self.failed) / self.total


class JobStore:
    """LRU-ish dict keyed by job id. Oldest jobs evicted past max_jobs_in_memory."""

    def __init__(self, max_jobs: int = settings.max_jobs_in_memory) -> None:
        self._jobs: "OrderedDict[str, Job]" = OrderedDict()
        self._max = max_jobs

    def create(self, kind: JobKind, urls: list[str]) -> Job:
        job = Job(
            kind=kind,
            total=len(urls),
            leads=[Lead(source_url=u) for u in urls],
        )
        self._jobs[job.id] = job
        self._evict()
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def list_recent(self, limit: int = 50) -> list[Job]:
        items = list(self._jobs.values())
        items.sort(key=lambda j: j.created_at, reverse=True)
        return items[:limit]

    def _evict(self) -> None:
        while len(self._jobs) > self._max:
            self._jobs.popitem(last=False)


store = JobStore()
