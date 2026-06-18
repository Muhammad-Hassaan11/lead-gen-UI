# Prospector — Build Plan

Companion to `specs.md`. This is the *how* and *when*.
`tasks.md` is the *what*.

---

## Build philosophy

The frontend is already designed and styled. The risk now lives in the backend
and in wiring the existing prototype scrapers into a clean async service.

**Order of risk (highest first):**

1. Maps scraping (Google actively defends — the DOM rots)
2. Wiring scrapers under one Playwright browser without leaks
3. Job-store lifecycle in FastAPI (BackgroundTasks + async generators)
4. Frontend ↔ backend wiring (CORS, streaming, polling)
5. CSV export edge cases (Excel quoting, UTF-8 BOM)

Front-load the risky scraper work. Save the wiring for last.

---

## Phase 0 — Backend scaffolding (already done as skeleton; finish it)

**Goal:** FastAPI app boots, `/healthz` returns `{"ok": true}`.

**Deliverables**
- `lead-scraper/requirements.txt` filled out.
- `app/main.py` with FastAPI app + CORS middleware + `/healthz` route.
- `app/utils/log.py` reused as-is.
- `run.sh` / `run.bat`.

**Exit:** `curl localhost:8000/healthz` returns 200.

---

## Phase 1 — Port scrapers from `scrape/` into `app/scrapers/`

**Goal:** Each scraper becomes an async function taking a URL, returning a
typed Pydantic model.

**Deliverables**
- `app/scrapers/browser.py` — Playwright singleton, UA + viewport rotation.
- `app/scrapers/maps.py` — `scrape_maps(url) -> MapsResult`.
- `app/scrapers/website.py` — `find_website(maps_url) -> str | None`.
- `app/scrapers/email.py` — `scrape_emails(url) -> list[str]`.
- `app/scrapers/facebook.py` — `find_facebook(url) -> str | None`.

**Exit:** Each scraper works standalone on 3 real URLs from the operator's
fixtures.

---

## Phase 2 — Orchestrator + job store

**Deliverables**
- `app/jobs.py` — in-memory `JobStore` with `Job` and `Lead` models.
- `app/pipeline.py` — `run_all(maps_url)` chains the four scrapers.
- `app/csv_export.py` — `leads_to_csv(leads) -> bytes` with UTF-8 BOM.

**Exit:** Calling `pipeline.run_all(url)` from a Python REPL returns a complete
`Lead` for a known-good Maps URL.

---

## Phase 3 — REST routes

**Deliverables**
- `POST /api/scrape/{maps|website|email|facebook|all}` — accepts
  `{"urls": [...]}`, creates a Job, returns `job_id`.
- `GET /api/jobs/{job_id}` — full job + leads.
- `GET /api/jobs/{job_id}/export.csv` — CSV download.
- `GET /api/jobs` — paginated last-50.

**Exit:** Every route returns valid JSON for happy + error paths. Tested with
`curl`.

---

## Phase 4 — CLI orchestrator (`main.py`)

**Goal:** Same logic, no HTTP. For overnight batches.

```
python main.py all      --urls urls.txt --out leads.csv
python main.py email    --urls sites.txt --out emails.csv
```

**Exit:** Both modes finish a 20-URL batch from the command line and produce
a valid CSV.

---

## Phase 5 — Frontend wiring

The UI is already designed (`Prospector.html` + `*.jsx`). What it needs:

**Deliverables**
- Replace mock pipeline in `app.jsx::runSearch` with `fetch('/api/scrape/...')`.
- Add scraper-kind tabs (All-in-One, Maps, Website, Email, Facebook) to the
  search panel.
- Add a "bulk paste" textarea sub-mode to every tab.
- Wire 1.5s polling on `/api/jobs/{id}` while `status === "running"`.
- Wire Export CSV to `GET /api/jobs/{id}/export.csv`.
- Show toast on failure with the backend error message.

**Exit:** Operator opens `Prospector.html`, pastes a Maps URL, clicks Run,
sees a row stream in.

---

## Phase 6 — Hardening + polish

**Deliverables**
- Per-stage logging via structlog.
- On Maps selector miss, take a screenshot to `data/debug/`.
- 5–10s jittered delay between bulk Maps requests.
- README with screenshots.
- Definition-of-Done checklist green.

---

## Decision gates

- **End of Phase 1:** If Maps scraping fails on 5/10 fixtures → freeze
  selectors as configurable and prompt operator for fresh ones.
- **End of Phase 5:** If the UI feels sluggish on a 50-URL batch → switch
  from polling to a Server-Sent Events stream.

---

## Estimated effort

| Phase                 | Effort |
|-----------------------|--------|
| 0 — Scaffold          | 0.5d   |
| 1 — Port scrapers     | 1.0d   |
| 2 — Orchestrator      | 0.5d   |
| 3 — REST routes       | 0.5d   |
| 4 — CLI               | 0.25d  |
| 5 — Frontend wiring   | 1.0d   |
| 6 — Polish            | 0.5d   |
| **Total**             | **~4.25d** |
