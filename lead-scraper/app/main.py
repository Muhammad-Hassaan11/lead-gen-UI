"""FastAPI entry point.

Run:
    uvicorn app.main:app --reload --port 8000

The frontend (Prospector.html) can be opened either:
  - directly via file:// (CORS is open), or
  - via http://localhost:8000/  (served from this app)
"""
from __future__ import annotations

import csv
import io
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.config import settings
from app.csv_export import leads_to_csv
from app.jobs import Job, JobKind, store
from app.pipeline import dispatch
from app.scrapers.browser import manager as browser_manager
from app.utils.log import configure_logging, logger
from app.utils.url import clean_urls

# Frontend lives in lead-scraper/frontend/
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


# ---- lifecycle --------------------------------------------------------------

@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(settings.log_level)
    logger.info("startup", host=settings.host, port=settings.port)
    yield
    await browser_manager.shutdown()
    logger.info("shutdown")


app = FastAPI(title="Prospector - Lead Scraper", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- schemas ---------------------------------------------------------------

class ScrapeRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=200)


class SingleScrapeRequest(BaseModel):
    maps_url: str = Field(..., min_length=1)


class BulkScrapeRequest(BaseModel):
    maps_urls: list[str] = Field(..., min_length=1, max_length=200)


class JobAccepted(BaseModel):
    job_id: str
    total: int
    status: str


# ---- API routes ------------------------------------------------------------

@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {"ok": True, "version": "1.0.0"}


def _start_job(kind: JobKind, urls: list[str], bg: BackgroundTasks) -> JobAccepted:
    urls = clean_urls(urls)
    if not urls:
        raise HTTPException(status_code=400, detail="No valid URLs provided.")
    job: Job = store.create(kind, urls)
    bg.add_task(dispatch, job)
    return JobAccepted(job_id=job.id, total=job.total, status=job.status)


@app.post("/api/scrape/maps", response_model=JobAccepted)
async def scrape_maps_route(req: ScrapeRequest, bg: BackgroundTasks) -> JobAccepted:
    return _start_job("maps", req.urls, bg)


@app.post("/api/scrape/website", response_model=JobAccepted)
async def scrape_website_route(req: ScrapeRequest, bg: BackgroundTasks) -> JobAccepted:
    return _start_job("website", req.urls, bg)


@app.post("/api/scrape/email", response_model=JobAccepted)
async def scrape_email_route(req: ScrapeRequest, bg: BackgroundTasks) -> JobAccepted:
    return _start_job("email", req.urls, bg)


@app.post("/api/scrape/facebook", response_model=JobAccepted)
async def scrape_facebook_route(req: ScrapeRequest, bg: BackgroundTasks) -> JobAccepted:
    return _start_job("facebook", req.urls, bg)


@app.post("/api/scrape/all", response_model=JobAccepted)
async def scrape_all_route(req: ScrapeRequest, bg: BackgroundTasks) -> JobAccepted:
    return _start_job("all", req.urls, bg)


@app.post("/api/scrape/single", response_model=JobAccepted)
async def scrape_single_route(req: SingleScrapeRequest, bg: BackgroundTasks) -> JobAccepted:
    return _start_job("all", [req.maps_url], bg)


@app.post("/api/scrape/bulk", response_model=JobAccepted)
async def scrape_bulk_route(req: BulkScrapeRequest, bg: BackgroundTasks) -> JobAccepted:
    return _start_job("all", req.maps_urls, bg)


@app.post("/api/scrape/csv", response_model=JobAccepted)
async def scrape_csv_route(bg: BackgroundTasks, file: UploadFile = File(...)) -> JobAccepted:
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV header row is required.")

    field_lookup = {name.strip().lower(): name for name in reader.fieldnames}
    maps_field = field_lookup.get("maps_url") or field_lookup.get("maps url")
    if maps_field is None:
        raise HTTPException(status_code=400, detail="CSV must include a maps_url column.")

    urls = [row.get(maps_field, "").strip() for row in reader]
    return _start_job("all", urls, bg)


@app.get("/api/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str) -> Job:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return job


@app.get("/api/jobs/{job_id}/export.csv")
async def export_csv(job_id: str) -> Response:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    data = leads_to_csv(job.leads)
    filename = f"prospector-{job.kind}-{job_id}.csv"
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/jobs", response_model=list[Job])
async def list_jobs(limit: int = 50) -> list[Job]:
    return store.list_recent(limit=limit)


# ---- Frontend serving -------------------------------------------------------

@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    html = FRONTEND_DIR / "Prospector.html"
    if not html.exists():
        raise HTTPException(status_code=404, detail="Prospector.html not found")
    return FileResponse(html)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


@app.get("/config.js", include_in_schema=False)
async def config_js() -> Response:
    return Response(
        content='window.__PROSPECTOR_CONFIG__ = {"apiBase": ""};\n',
        media_type="application/javascript",
    )


@app.get("/{name}.jsx", include_in_schema=False)
async def serve_jsx(name: str) -> FileResponse:
    f = FRONTEND_DIR / f"{name}.jsx"
    if not f.exists():
        raise HTTPException(status_code=404)
    return FileResponse(f, media_type="application/javascript")


@app.get("/styles.css", include_in_schema=False)
async def serve_css() -> FileResponse:
    f = FRONTEND_DIR / "styles.css"
    if not f.exists():
        raise HTTPException(status_code=404)
    return FileResponse(f, media_type="text/css")
