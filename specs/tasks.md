# Prospector — Task Checklist

Atomic tasks grouped by phase (see `plan.md`).
Legend: 🔴 blocker · 🟡 important · 🟢 nice-to-have

---

## Phase 0 — Backend scaffolding

- [x] 🔴 Fill `lead-scraper/requirements.txt`
- [x] 🔴 Write `app/main.py` (FastAPI + CORS + `/healthz`)
- [x] 🔴 Keep `app/utils/log.py` as-is (structlog config)
- [x] 🔴 Write `app/utils/url.py` (normalize, validate)
- [x] 🟡 Write `run.sh` and `run.bat`
- [x] 🔴 **Exit:** `curl localhost:8000/healthz` returns 200

---

## Phase 1 — Port scrapers

- [x] 🔴 `app/scrapers/browser.py` — Playwright singleton + UA/viewport rotation
- [x] 🔴 `app/scrapers/maps.py` — `scrape_maps(url) -> MapsResult` with dated selectors
- [x] 🔴 `app/scrapers/website.py` — `find_website(maps_url) -> str | None`
- [x] 🔴 `app/scrapers/email.py` — `scrape_emails(url) -> list[str]` with JUNK_FILTERS
- [x] 🔴 `app/scrapers/facebook.py` — `find_facebook(url) -> str | None`
- [x] 🟡 Phone extractor inlined via `phonenumbers` in maps.py

---

## Phase 2 — Orchestrator + jobs

- [x] 🔴 `app/jobs.py` — `JobStore`, `Job`, `Lead` Pydantic models
- [x] 🔴 `app/pipeline.py` — `run_all(maps_url) -> Lead` (Maps → Web → Email+FB)
- [x] 🔴 `app/csv_export.py` — `leads_to_csv(leads) -> bytes`, UTF-8 BOM, Excel-safe quoting
- [x] 🟡 Per-stage `status` updates so UI can stream progress

---

## Phase 3 — REST routes

- [x] 🔴 `POST /api/scrape/maps`
- [x] 🔴 `POST /api/scrape/website`
- [x] 🔴 `POST /api/scrape/email`
- [x] 🔴 `POST /api/scrape/facebook`
- [x] 🔴 `POST /api/scrape/all`
- [x] 🔴 `GET /api/jobs/{job_id}`
- [x] 🔴 `GET /api/jobs/{job_id}/export.csv`
- [x] 🔴 `GET /api/jobs` (paginated)
- [x] 🟡 Error handlers return JSON, not HTML

---

## Phase 4 — CLI

- [x] 🔴 `lead-scraper/main.py` — argparse-driven CLI
- [x] 🔴 Subcommands: `maps`, `website`, `email`, `facebook`, `all`
- [x] 🔴 `--urls <file>` and `--out <file>` flags
- [x] 🟡 Progress bar in CLI mode

---

## Phase 5 — Frontend wiring

- [x] 🔴 Replace mock `runSearch` with `fetch` to backend
- [x] 🔴 Add scraper-kind tabs (All-in-One / Maps / Website / Email / Facebook)
- [x] 🔴 Bulk-paste textarea sub-mode in every tab
- [x] 🔴 1.5s polling of `/api/jobs/{id}` while running
- [x] 🔴 Wire `Export CSV` to `GET /api/jobs/{id}/export.csv`
- [x] 🟡 Show toast on backend error
- [x] 🟡 Update data shape in `table.jsx` to match new `Lead` model
- [x] 🟡 Empty-state copy when no leads yet

---

## Phase 6 — Polish

- [x] 🟡 Top-level `README.md` with quickstart
- [x] 🟡 `CLAUDE.md` and `AGENT.md`
- [ ] 🟡 Screenshot the UI for the README
- [ ] 🟢 Tag `v1.0.0`
- [ ] 🟢 Troubleshooting section in README

---

## Stretch (post-v1)

- [ ] WebSocket / SSE streaming instead of polling
- [ ] Proxy rotation
- [ ] CEO / decision-maker finder
- [ ] Google Sheets sink (optional, behind a flag)
- [ ] Email verification (MX + SMTP RCPT TO)
