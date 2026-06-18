# Prospector — Build Spec (v1)

A local-first lead-generation workspace. The operator pastes Google Maps URLs
or business websites; the system extracts structured contact data and exports
it as CSV.

---

## 1. Goals & non-goals

**Goals**
- Four independent scrapers, each addressable from the UI: **Maps**, **Website**,
  **Email**, **Facebook**.
- One **All-in-One** pipeline that chains them: `Maps → Website → Email + Facebook`.
- Single-URL mode AND bulk-paste mode for every scraper.
- Live progress feed in the UI (rows stream in as they complete).
- CSV export of any result set, full or filtered.
- Runs entirely on the operator's laptop. No paid APIs.

**Non-goals (v1)**
- Google Sheets integration. CSV export is enough.
- Authentication, accounts, multi-tenant.
- CRM integrations.
- A persistent database. In-memory job store is enough — operator exports
  CSV before closing the tab.

---

## 2. Tech stack

| Layer       | Choice                                |
|-------------|---------------------------------------|
| Language    | Python 3.11+                          |
| API         | FastAPI + uvicorn                     |
| Scraping    | Playwright (async, Chromium)          |
| Validation  | Pydantic v2                           |
| HTTP client | httpx                                 |
| Phones      | `phonenumbers`                        |
| Logging     | structlog                             |
| Frontend    | Plain HTML + React (Babel-in-browser) |

No build step on the frontend. No npm, no webpack, no bundler.

---

## 3. Architecture

```
[Prospector.html / React]
        |
        |  fetch (CORS open to localhost)
        v
[FastAPI app — lead-scraper/app/main.py]
        |
        v
[pipeline.py orchestrator]
        |
        |   one async function per scraper
        v
maps.py  website.py  email.py  facebook.py
        |
        v
[JobStore (in-memory dict, jobs.py)]
        |
        v
GET /api/jobs/{id}/results  →  JSON
GET /api/jobs/{id}/export   →  CSV
```

One process. One Playwright browser instance, reused across requests.
Each request gets a fresh context with rotated UA + viewport.

---

## 4. Folder layout

```
lead generation/
├── Prospector.html
├── app.jsx  shell.jsx  table.jsx  data.jsx
├── styles.css
├── CLAUDE.md  AGENT.md  README.md
├── scrape/                         # original prototype scripts (reference)
└── lead-scraper/
    ├── app/
    │   ├── main.py                 # FastAPI routes
    │   ├── pipeline.py             # orchestrator
    │   ├── jobs.py                 # in-memory job store
    │   ├── csv_export.py           # CSV serializer
    │   ├── scrapers/
    │   │   ├── maps.py
    │   │   ├── website.py
    │   │   ├── email.py
    │   │   ├── facebook.py
    │   │   └── browser.py          # shared Playwright lifecycle
    │   └── utils/
    │       ├── log.py
    │       └── url.py
    ├── main.py                     # CLI orchestrator (no FastAPI)
    ├── requirements.txt
    ├── run.sh / run.bat
    └── README.md
```

---

## 5. Lead schema

A single canonical record shape returned from every endpoint:

```python
class Lead(BaseModel):
    id: str                # uuid4
    source_url: str        # what the operator pasted
    business_name: str | None
    address: str | None
    phone: str | None
    website: str | None
    emails: list[str]      # cleaned + deduped
    facebook: str | None
    status: Literal["pending", "running", "done", "failed", "partial"]
    error: str | None
    elapsed_ms: int | None
```

Empty fields are `None` / `[]`. Never invent data.

---

## 6. API contract

All routes prefixed `/api`. JSON in/out unless noted.

### Health

```
GET /healthz  →  {"ok": true, "version": "1.0.0"}
```

### Scrape

Every scrape endpoint accepts the same shape:

```json
{ "urls": ["...", "..."] }     // max 200
```

| Endpoint                  | Input type              | Output per input                |
|---------------------------|-------------------------|---------------------------------|
| `POST /api/scrape/maps`   | Google Maps place URL   | name, address, phone, website   |
| `POST /api/scrape/website`| Google Maps place URL   | website only                    |
| `POST /api/scrape/email`  | Business website URL    | emails                          |
| `POST /api/scrape/facebook`| Business website URL   | facebook URL                    |
| `POST /api/scrape/all`    | Google Maps place URL   | everything (Maps→Web→Email+FB)  |

Response (immediate):

```json
{ "job_id": "uuid", "total": 12, "status": "running" }
```

### Job tracking

```
GET  /api/jobs/{job_id}            →  full job object incl. nested leads
GET  /api/jobs/{job_id}/export.csv →  CSV download
GET  /api/jobs                     →  paginated list (last 50)
```

A "job object" looks like:

```json
{
  "id": "uuid",
  "kind": "all",
  "status": "running",
  "total": 12,
  "done": 7,
  "failed": 0,
  "created_at": "ISO8601",
  "leads": [ ...Lead... ]
}
```

---

## 7. Module specs

### 7.1 `scrapers/browser.py`

Shared Playwright lifecycle:

- `get_browser()` — returns the singleton `Browser` (lazy-launched, headless).
- `new_context()` — random UA from a pool of 10, random viewport from 3.
- `shutdown()` — called from FastAPI shutdown event.

### 7.2 `scrapers/maps.py`

```python
async def scrape_maps(url: str) -> MapsResult
```

Returns `name`, `address`, `phone`, `website`. Uses selectors:

| Field   | Selector                                                          |
|---------|-------------------------------------------------------------------|
| name    | `h1.DUwDvf, h1[class*="fontHeadlineLarge"]`                       |
| website | `a[data-item-id="authority"]`                                     |
| phone   | `button[data-item-id^="phone:tel:"] div.fontBodyMedium`           |
| address | `button[data-item-id="address"] div.fontBodyMedium`               |

Selectors live at the top of the file with a `LAST_VERIFIED = "2026-06-18"` constant.

Sequential, jittered 5–10s delay between requests in bulk mode (Maps anti-ban).

### 7.3 `scrapers/website.py`

```python
async def find_website(maps_url: str) -> str | None
```

Same as `scrape_maps` but extracts only the website. Used when the operator
just wants the website field without the rest.

### 7.4 `scrapers/email.py`

```python
async def scrape_emails(url: str) -> list[str]
```

Flow:
1. `goto(url, wait_until="domcontentloaded")` + 4s settle.
2. Collect emails from: `mailto:` hrefs → page text → raw HTML.
3. If nothing found, follow links matching `/contact|/about|/team|/support`
   (max 3 follow-ups).
4. Clean each email through `JUNK_FILTERS`:
   - Reject `wixpress.com`, `sentry.io`, `example.com`, `mysite.com`, etc.
   - Reject local-parts matching image filenames (`logo@2x`, 32-char hex blobs).
   - Reject local-parts `noreply`, `donotreply`, `mailer-daemon`.
   - Normalize: lowercase, strip `mailto:`, dedupe.

### 7.5 `scrapers/facebook.py`

```python
async def find_facebook(url: str) -> str | None
```

Parse all `a[href]`, return first match for `facebook.com/<page>` that isn't
`sharer`, `dialog`, or `plugins`. Fallback: regex against raw page HTML.

### 7.6 `pipeline.py`

```python
async def run_all(maps_url: str) -> Lead
```

`Maps → Website → (email + facebook in parallel)`. If Maps yields no website,
return what we have with `status="partial"`.

### 7.7 `jobs.py`

In-memory:

```python
JOBS: dict[str, Job] = {}
```

No thread-safety needed — FastAPI BackgroundTasks runs in the same event loop.
Process restart wipes jobs. The CSV is the persistence layer.

---

## 8. Frontend (the UI in `/Prospector.html`)

Layout:

- Left sidebar — Workspace nav, credits widget, settings.
- Header — title, theme toggle, avatar.
- Main panel — `SearchPanel` with **scraper-type tabs at the top**:
  - **All-in-One** (Maps → everything)
  - **Maps** (place info only)
  - **Website** (Maps → website)
  - **Email** (website → emails)
  - **Facebook** (website → FB)
- Each tab supports **Single URL** or **Bulk URLs (textarea)** sub-mode.
- Results stream into a sortable table below.
- Toolbar above the table: search box, filter pills, Export CSV.
- Click a row → drawer with full lead details.
- Selection bar floats at bottom when ≥1 row checked.

Theme: light/dark toggle, persisted in `localStorage`.

The UI talks to `http://localhost:8000` via `fetch`. While a job is `running`,
poll `/api/jobs/{id}` every 1.5s and append new leads as they appear.

---

## 9. CLI orchestrator (`lead-scraper/main.py`)

```bash
python main.py all      --urls urls.txt --out leads.csv
python main.py maps     --urls urls.txt --out leads.csv
python main.py email    --urls sites.txt --out emails.csv
python main.py facebook --urls sites.txt --out fb.csv
```

Same logic as the FastAPI endpoints, but without the server. Handy when the
operator wants to run a 200-URL batch overnight via cron / Task Scheduler.

---

## 10. Anti-ban rules

- Maps: sequential, 5–10s jittered delay per request, max 1 concurrent.
- Websites: max 5 concurrent across the whole job.
- UA pool of 10, viewport pool of 3 — rotated per browser context.
- One browser context per 25 leads, then close + reopen.
- If a request times out twice on the same URL, mark `failed` and move on.

---

## 11. Configuration (`.env`, optional)

```ini
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO
MAPS_MIN_DELAY_SEC=5
MAPS_MAX_DELAY_SEC=10
WEBSITE_CONCURRENCY=5
WEBSITE_TIMEOUT_SEC=20
DEFAULT_PHONE_REGION=US
HEADLESS=true
```

Defaults are sane. The operator should never have to touch this for v1.

---

## 12. Definition of Done (v1)

- [ ] All four scraper endpoints work against 10 real URLs each.
- [ ] All-in-One pipeline completes a 20-URL batch without ban.
- [ ] CSV export round-trips through Excel and Google Sheets without breakage
      (proper quoting, UTF-8 BOM).
- [ ] The UI handles `partial` and `failed` states distinctly.
- [ ] Frontend opens with `file://Prospector.html` AND with `python -m http.server`
      — both must talk to `localhost:8000`.
- [ ] README has the install + run commands a stranger could follow.
