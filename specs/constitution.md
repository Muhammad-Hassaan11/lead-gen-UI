# Prospector — Project Constitution

The fourth doc. `specs.md` = what. `plan.md` = how/when. `tasks.md` = next move.
**This one = why, and the rules of engagement.**

When in doubt during a build decision, this file wins over the other three.
Specs change, plans slip, tasks reshuffle — principles don't.

---

## Article I — Purpose

This project exists to **save the operator hours of manual lead research per
day** by automating the journey from `Google Maps link → enriched contact row
→ CSV`.

It is a personal productivity tool, not a SaaS product. Every decision is
judged by one question:

> "Does this make the operator's daily workflow faster or more reliable?"

If a feature, abstraction, or piece of infrastructure does not answer "yes"
to that question, it does not belong in v1.

---

## Article II — Core principles

### 1. Simplicity over cleverness

Boring code, common patterns, obvious names. Anyone reading the codebase six
months from now should be able to follow it without a map. No metaprogramming,
no clever decorators, no DSLs.

### 2. Local-first, free by default

The whole system runs on one laptop with no paid services. Free tiers are a
deliberate constraint that forces resourcefulness. Paid APIs (Apollo, Hunter,
paid proxies) are **opt-in escape hatches**, never the default path.

### 3. Visibility over magic

Every stage of the pipeline produces an observable artifact: a logged event, a
job-status update, a screenshot on Maps failure. When something breaks (and
it will), the operator should be able to point at exactly which stage and why
within 60 seconds.

### 4. Fail loud, fail isolated

A failure in one lead never poisons the rest of a batch. One bad Maps URL
must not stop the other 49. Errors are captured per-lead, surfaced in the
UI, and never silently swallowed. Empty fields are acceptable; corrupted data
is not.

### 5. Honesty over impressiveness

A confidence-low result is shown as low. A missed field is shown as `—`, not
a fabricated value. A bulk job of 50 URLs that completed 47 shows `47/50`,
not `47 successes`. The number is the truth.

### 6. Selectors and heuristics are temporary

Anything that scrapes a third-party website is built on sand. Google will
change its DOM. Websites will redesign. Treat scraping selectors as
**disposable infrastructure** — kept in single, well-named files, dated, easy
to swap. Never embed them deep in business logic.

### 7. The UI is the deliverable

The operator stares at this app every day. A pipeline that works perfectly
but has a clunky UI is a failure. Polish the surface the operator touches.

---

## Article III — Operating reality

This project is built on three uncomfortable truths.

1. **Google actively defends Maps against scraping.** Some weeks the scraper
   works flawlessly. Some weeks it hits CAPTCHA on the third request. Plan
   for it. The UI must communicate it.
2. **Free scraping is fragile by definition.** No guarantees. The README
   says so plainly.
3. **Heuristics are wrong sometimes.** Email regex catches junk. The
   operator is the final filter — the tool is a force-multiplier, not an
   oracle.

---

## Article IV — Ethical floor

This project scrapes publicly visible business information for direct
outreach. That is normal commercial practice. The line still matters.

### What we do
- Scrape **business contact info** (company emails, phones, public profiles)
  from publicly accessible pages.
- Aggregate it into a CSV the operator uses for legitimate outreach.

### What we do not do
- **No personal/private data.** Home addresses, personal mobiles, family
  details. If the scraper accidentally captures something like this, it's
  the operator's job to remove it before use.
- **No paywalled or auth-gated content.**
- **No deceptive identification.** Honest UA. Not pretending to be Googlebot.
- **No mass spam.** This tool produces leads for **considered, personalized
  outreach**. What the operator does is on the operator, but the README
  states the intended use.
- **No selling or republishing the scraped data.**

The operator is responsible for compliance with applicable laws in their
jurisdiction and the jurisdictions of the businesses scraped (GDPR, CAN-SPAM,
PECR, etc.). The tool does not — and cannot — enforce this for them.

---

## Article V — Code standards

- **Python 3.11+, type hints everywhere.**
- **Pydantic v2 for boundaries.** Anything crossing an HTTP boundary is a
  Pydantic model.
- **No global state.** Settings come from `app.config`. Browser context
  passed explicitly.
- **Async everywhere I/O touches.** `httpx.AsyncClient`,
  `playwright.async_api`.
- **Functions over classes.** Classes only for Pydantic models and config.
- **No comments explaining *what* the code does.** Only *why*. If a `what`
  comment seems needed, the code needs a better name.
- **Selectors at the top of the scraper file, dated.**

Frontend:
- **No build step.** Babel-in-browser, plain `.jsx`.
- **No imports.** Attach to `window` via `Object.assign(window, ...)`.
- **CSS custom properties** for theming. Light + dark from one stylesheet.

---

## Article VI — Anti-scope (what v1 does NOT include)

- ❌ User accounts / authentication
- ❌ A persistent database (in-memory job store + CSV export is enough)
- ❌ Google Sheets integration (CSV is the deliverable)
- ❌ CRM integrations (HubSpot, Salesforce, Pipedrive)
- ❌ Email-sending features
- ❌ Lead scoring / ranking ML
- ❌ Browser extension / native mobile app
- ❌ Docker / Kubernetes / cloud deployment

Any of these may be reasonable in v2+. None belong in v1.

---

## Article VII — Decision-making

When facing a design choice, stop at the first that gives a clear answer:

1. **Does the constitution speak to it?**
2. **Does the spec speak to it?** `specs.md` is the canonical contract.
3. **What does the operator's daily workflow need?**
4. **What is the simplest thing that could possibly work?**
5. **What can we change later cheaply?**

If none of these give a clear answer, write down the question and pick
something. Don't deliberate for more than 30 minutes on a v1 decision.

---

## Article VIII — Honesty clauses

- **The README does not oversell.** No "AI-powered". No "enterprise-grade".
- **Documentation matches reality.** When the code changes, the docs change
  in the same commit.
- **Failures are visible, not hidden.** `3/10` is the truth.

---

*Version 1.0 — ratified at project start.*
