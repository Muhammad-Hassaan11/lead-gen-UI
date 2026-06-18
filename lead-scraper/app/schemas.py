from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MapsScrapeRequest(BaseModel):
    maps_url: str


class BulkScrapeRequest(BaseModel):
    maps_urls: list[str] = Field(min_length=1, max_length=200)


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    maps_url: str
    business_name: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    emails: list[str] = Field(default_factory=list)
    facebook: str | None = None
    linkedin: str | None = None
    instagram: str | None = None
    twitter: str | None = None
    ceo_name: str | None = None
    ceo_linkedin: str | None = None
    source_pages: list[str] = Field(default_factory=list)
    status: str
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    mode: str
    total: int
    done: int
    failed: int
    status: str
    leads: list[LeadOut] = Field(default_factory=list)
