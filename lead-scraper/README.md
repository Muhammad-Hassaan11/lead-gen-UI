# lead-scraper

FastAPI backend for **Prospector**. Wraps four Playwright scrapers
(Maps / Website / Email / Facebook) behind a small REST surface that the
React UI (in the parent directory) talks to.

## Quick start

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium

# Run
./run.sh                # macOS / Linux
run.bat                 # Windows
# or: uvicorn app.main:app --reload --port 8000
```

Smoke check:

```bash
curl http://localhost:8000/healthz
# {"ok": true, "version": "1.0.0"}
```

## API

| Method | Path                              | Description                          |
|--------|-----------------------------------|--------------------------------------|
| GET    | `/healthz`                        | Health probe                         |
| POST   | `/api/scrape/maps`                | Maps URLs → name/address/phone/web   |
| POST   | `/api/scrape/website`             | Maps URLs → website only             |
| POST   | `/api/scrape/email`               | Website URLs → emails                |
| POST   | `/api/scrape/facebook`            | Website URLs → Facebook URL          |
| POST   | `/api/scrape/all`                 | Maps URLs → everything               |
| GET    | `/api/jobs/{id}`                  | Full job + nested leads              |
| GET    | `/api/jobs/{id}/export.csv`       | Download job as CSV                  |
| GET    | `/api/jobs`                       | Last 50 jobs                         |

Every scrape endpoint accepts `{"urls": [...]}` (max 200 per call) and returns
`{"job_id": "...", "total": N, "status": "..."}`.

## CLI (no server)

```bash
python main.py all      --urls urls.txt --out leads.csv
python main.py maps     --urls urls.txt --out leads.csv
python main.py website  --urls urls.txt --out websites.csv
python main.py email    --urls sites.txt --out emails.csv
python main.py facebook --urls sites.txt --out facebook.csv
```

One URL per line. Lines starting with `#` are ignored.

## Layout

```
lead-scraper/
├── app/
│   ├── main.py             # FastAPI routes
│   ├── pipeline.py         # orchestrator (Maps → Web → Email + FB)
│   ├── jobs.py             # in-memory Job + Lead store
│   ├── csv_export.py       # UTF-8 BOM CSV serializer
│   ├── config.py           # pydantic-settings
│   ├── scrapers/
│   │   ├── browser.py      # Playwright lifecycle, UA + viewport pool
│   │   ├── maps.py         # Google Maps place scraper
│   │   ├── website.py      # Maps URL → website extractor
│   │   ├── email.py        # website → emails (with junk filters)
│   │   └── facebook.py     # website → Facebook URL
│   └── utils/
│       ├── log.py          # structlog
│       └── url.py          # helpers
├── main.py                 # CLI batch runner
├── requirements.txt
├── run.sh / run.bat
└── .env.example
```

## Config

Optional `.env`:

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

## Maintaining the Maps scraper

Google rewrites the Maps DOM every few months. Selectors live in
`app/scrapers/maps.py` at the top, alongside a `LAST_VERIFIED` constant. When
fields stop returning, the playbook is:

1. Open a Maps URL in your browser, dev-tools.
2. Inspect the element that holds the field you want.
3. Update the selector constant.
4. Bump the date.

That's the whole maintenance loop — there's nothing else to patch.

## Job lifecycle

```
POST /api/scrape/...      → create Job (pending), spawn BackgroundTask
BackgroundTask runs       → leads flip from pending → running → done/failed
GET /api/jobs/{id}        → snapshot (UI polls this every 1.5s)
GET /api/jobs/{id}/export.csv → download
```

Jobs live in memory. Process restart wipes them. That's by design — the CSV
is the persistence layer.
