# CLAUDE.md — Project Memory

> Read this first when joining the project. Everything you need to navigate the
> codebase, run it, and not break things lives here.

## What this is

**Prospector / Lead-Scraper** is a local-first lead-generation workspace. The
operator pastes Google Maps URLs (or business websites), and the system extracts:

- Business name + address + phone (from Maps)
- Official website
- Public emails (from website)
- Facebook page (from website)
- (Optional) Decision-maker name / LinkedIn

Results land in a sortable, exportable table. Everything runs on the operator's
laptop. No paid APIs. No external state.

## Repo layout

```
lead generation/
├── Prospector.html         # entry point — open this in a browser
├── app.jsx  shell.jsx      # React UI (Babel-in-browser, no build step)
├── table.jsx  data.jsx
├── styles.css
├── scrape/                 # original standalone Playwright scripts
│   ├── scraper.py          # Selenium Google Maps search prototype
│   ├── website_scraper.py  # Maps URL  -> website
│   ├── emails_scraper.py   # website   -> emails
│   ├── facebook_scraper.py # website   -> Facebook URL
│   └── main.py             # orchestrator (Maps -> Website -> Email + FB)
├── lead-scraper/           # FastAPI service that wraps the scrapers
│   ├── app/
│   │   ├── main.py         # FastAPI app + REST routes
│   │   ├── pipeline.py     # orchestrator
│   │   ├── scrapers/       # maps.py / website.py / email.py / facebook.py
│   │   ├── jobs.py         # in-memory job tracker
│   │   ├── csv_export.py   # CSV serializer
│   │   └── utils/log.py
│   ├── requirements.txt
│   ├── run.sh
│   └── README.md
└── specs/                  # constitution.md / plan.md / tasks.md / specs.md
```

## How to run (TL;DR)

```bash
# 1. Backend
cd lead-scraper
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --port 8000

# 2. Frontend
# Open ../Prospector.html in a browser. The UI talks to localhost:8000.
```

## Architecture in one diagram

```
[Prospector.html / React UI]
            |
            | fetch('/api/scrape/...')
            v
[FastAPI app — lead-scraper/app/main.py]
            |
            v
[pipeline.py orchestrator]
            |
   +--------+--------+----------+
   |        |        |          |
   v        v        v          v
maps.py  website.py  email.py  facebook.py
   (Playwright, async, headless)
            |
            v
[in-memory Job store -> JSON / CSV]
```

## Core conventions

- **Python 3.11+**, async-first. All scrapers expose `async def scrape_*()`.
- **Pydantic v2** at every HTTP boundary.
- **Playwright async API**. One browser per FastAPI process, contexts rotated.
- **No DB in v1.** Jobs and results live in `app.jobs.JobStore` (in-memory).
  CSV export is the persistence layer.
- **Frontend = no build step.** Plain HTML + Babel-in-browser JSX. Edit a
  `.jsx` file, refresh the tab, done.
- **CORS is open to `localhost`** so `file://Prospector.html` can talk to
  `localhost:8000`.

## Things that will trip you up

- The frontend is React, but it uses Babel standalone — `import` statements
  will NOT work. Everything attaches to `window` via `Object.assign(window, ...)`.
- `scrape/` contains the **original prototype scripts** the user wrote in
  Roman-Urdu comments. The production code in `lead-scraper/app/scrapers/`
  re-implements the same logic, cleaned up.
- The Google Maps DOM changes every few months. Selectors live in
  `lead-scraper/app/scrapers/maps.py` at the top of the file with a
  "last verified" date — update both together.
- Email scraping uses a junk-filter list (`wixpress.com`, `sentry.io`, image
  filenames, etc.) — see `app/scrapers/email.py::JUNK_FILTERS`.

## Where to start a change

| You want to...                          | Edit                                       |
|-----------------------------------------|--------------------------------------------|
| Change Maps selectors                   | `lead-scraper/app/scrapers/maps.py`        |
| Add a new field to the leads table      | `lead-scraper/app/scrapers/*.py` + `table.jsx` |
| Add a new "scraper tab" in the UI       | `shell.jsx` (SearchPanel) + a route in `main.py` |
| Change the CSV format                   | `lead-scraper/app/csv_export.py` + `app.jsx::exportCSV` |
| Tweak look & feel                       | `styles.css`                                |
| Add a new API endpoint                  | `lead-scraper/app/main.py`                  |

## See also

- `AGENT.md` — operating instructions for an AI agent working in this repo
- `specs/specs.md` — full v1 contract (canonical)
- `specs/constitution.md` — why / non-negotiables
- `specs/plan.md` — phased build plan
- `specs/tasks.md` — atomic task checklist
