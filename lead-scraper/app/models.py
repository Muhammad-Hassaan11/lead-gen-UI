from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mode: Mapped[str] = mapped_column(Text, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")

    leads: Mapped[list[Lead]] = relationship(
        "Lead",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (Index("ix_leads_maps_url_unique", "maps_url", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    maps_url: Mapped[str] = mapped_column(Text, nullable=False)
    business_name: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    _emails: Mapped[str] = mapped_column("emails", Text, nullable=False, default="[]")
    facebook: Mapped[str | None] = mapped_column(Text)
    linkedin: Mapped[str | None] = mapped_column(Text)
    instagram: Mapped[str | None] = mapped_column(Text)
    twitter: Mapped[str | None] = mapped_column(Text)
    ceo_name: Mapped[str | None] = mapped_column(Text)
    ceo_linkedin: Mapped[str | None] = mapped_column(Text)
    _source_pages: Mapped[str] = mapped_column("source_pages", Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    job: Mapped[Job] = relationship("Job", back_populates="leads")

    @property
    def emails(self) -> list[str]:
        return _loads_list(self._emails)

    @emails.setter
    def emails(self, values: Sequence[str] | None) -> None:
        self._emails = _dumps_list(values)

    @property
    def source_pages(self) -> list[str]:
        return _loads_list(self._source_pages)

    @source_pages.setter
    def source_pages(self, values: Sequence[str] | None) -> None:
        self._source_pages = _dumps_list(values)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _loads_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        values = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(values, list):
        return []
    return [str(value) for value in values]


def _dumps_list(values: Sequence[str] | None) -> str:
    return json.dumps(list(values or []))


@event.listens_for(Job, "before_insert")
def _set_job_created_at(_mapper: object, _connection: object, target: Job) -> None:
    if target.created_at is None:
        target.created_at = _utcnow()


@event.listens_for(Lead, "before_insert")
def _set_lead_timestamps(_mapper: object, _connection: object, target: Lead) -> None:
    now = _utcnow()
    if target.created_at is None:
        target.created_at = now
    if target.updated_at is None:
        target.updated_at = now


@event.listens_for(Lead, "before_update")
def _touch_lead_updated_at(_mapper: object, _connection: object, target: Lead) -> None:
    target.updated_at = _utcnow()
