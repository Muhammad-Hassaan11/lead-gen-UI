# Prospector — Lead Generation Workspace

Local-first lead-generation tool. Paste a Google Maps URL (or a list of them)
and get back business name, address, phone, website, emails, and Facebook page.
Export anything as CSV.

Runs on your laptop. No paid APIs. No accounts.

```
+----------------------------------+    +-------------------------+
|   Prospector.html (React UI)     |    |  lead-scraper (FastAPI) |
|   - All-in-One / Maps / Website  |    |  - /api/scrape/{kind}   |
|   - Email / Facebook tabs        |  - |  - Playwright           |
|   - Live progress + CSV export   |    |  - in-memory job store  |
+----------------------------------+    +-------------------------+
```

## Quick start

### 1. Install the backend

```bash
cd lead-scraper
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### 2. Run the backend

```bash
# Windows
run.bat

# macOS / Linux
./run.sh
```

The API is now live at `http://127.0.0.1:8000`. Check with:

```bash
curl http://127.0.0.1:8000/healthz
# {"ok": true, "version": "1.0.0"}
```

### 3. Open the UI

Double-click `Prospector.html`. That's it — no build step. The page talks to
`localhost:8000`. The sidebar shows a green **connected** pill when the
backend is reachable.

If you'd rather serve the UI over HTTP (some browsers block `file://` fetch):

```bash
# from the repo root
python -m http.server 5500
# then open http://localhost:5500/Prospector.html
```

## What the UI does

The search panel has five tabs at the top — each one drives a different
scraper:

| Tab          | Input                  | Returns                                |
|--------------|------------------------|----------------------------------------|
| All-in-One   | Google Maps place URL  | name, address, phone, website, emails, Facebook |
| Maps         | Google Maps place URL  | name, address, phone, website          |
| Website      | Google Maps place URL  | website only                           |
| Email        | Business website URL   | de-junked emails                       |
| Facebook     | Business website URL   | Facebook page URL                      |

Each tab supports **Single** (one URL) or **Bulk** (paste up to 200, one per
line) input. Results stream into the table below as they finish — you can
search, sort, filter, and **Export CSV** at any point.

## What's where

```
lead generation/
├── Prospector.html             # entry point — open this
├── app.jsx  shell.jsx          # React UI
├── table.jsx  data.jsx
├── styles.css
├── CLAUDE.md  AGENT.md         # project memory for AI assistants
├── README.md                   # this file
├── specs/                      # the four-doc design system
│   ├── specs.md  plan.md
│   ├── tasks.md  constitution.md
├── scrape/                     # original Playwright/Selenium prototypes
│   ├── scraper.py              # Selenium Maps query (legacy)
│   ├── website_scraper.py      # Maps URL → website
│   ├── emails_scraper.py       # website → emails
│   ├── facebook_scraper.py     # website → Facebook
│   └── main.py                 # all-in-one CLI (uses the modules above)
└── lead-scraper/               # production FastAPI service
    ├── app/                    # main.py, pipeline.py, scrapers/, jobs.py …
    ├── main.py                 # CLI batch runner (no server)
    ├── requirements.txt
    ├── run.sh / run.bat
    └── README.md
```

## Running batches without the UI

If you want to run a big job overnight, skip the browser and use the CLI:

```bash
cd lead-scraper
# urls.txt is one URL per line
python main.py all      --urls urls.txt --out leads.csv
python main.py email    --urls sites.txt --out emails.csv
python main.py facebook --urls sites.txt --out facebook.csv
```

The CSV opens cleanly in Excel and Google Sheets (UTF-8 BOM, CRLF, fully quoted).

## Things to know

- **Google Maps fights scraping.** Sequential requests with 5–10s jittered
  delays is the default. If you hit a CAPTCHA, walk away for a few hours.
- **Headless by default.** Set `HEADLESS=false` in `lead-scraper/.env` to
  watch what Playwright is doing.
- **Job state is in-memory.** Close the backend and history is gone. The CSV
  is the persistence layer — export what you care about.
- **DOM selectors rot.** `lead-scraper/app/scrapers/maps.py` has a
  `LAST_VERIFIED` constant at the top. If Maps stops working, update the
  selectors and bump the date.

## Ethical use

This tool scrapes **publicly visible business contact info** for legitimate
outreach. It does not handle personal data, paywalled content, or auth-gated
pages. You're responsible for compliance with applicable laws in your
jurisdiction (GDPR, CAN-SPAM, PECR, etc.). Don't use it for spam.

See `specs/constitution.md` for the full ethical floor.

## Troubleshooting

| Symptom                                 | Fix                                              |
|-----------------------------------------|--------------------------------------------------|
| Sidebar shows "offline"                 | Backend not running. Start `lead-scraper/run.sh`.|
| Maps returns empty fields               | DOM probably changed. Update selectors in `lead-scraper/app/scrapers/maps.py`. |
| `playwright install` fails              | Check your network. You need ~150 MB.            |
| CSV download does nothing               | Run a job first, then click Export.              |
| Browser blocks `fetch` from `file://`   | Serve the UI with `python -m http.server 5500`.  |

---

For AI agents: read `CLAUDE.md` and `AGENT.md` first.
