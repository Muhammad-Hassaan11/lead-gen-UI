# AGENT.md — Operating Manual for AI Agents

> If you're an AI assistant working on this repo, read CLAUDE.md first for the
> map, then this file for the rules.

## Mission

This codebase exists to **save the operator hours of manual lead research**.
Every change is judged by one question:

> "Does this make the operator's daily workflow faster or more reliable?"

If the answer is "no", do not make the change.

## Hard rules

1. **Never call paid APIs.** No Apollo, no Hunter, no Clearbit, no paid proxies.
   The whole point of this tool is that the operator can run it on a laptop
   with zero recurring cost.
2. **Never scrape gated content.** If a page requires login, walk away.
3. **Never parallelize Google Maps requests.** Sequential, 15–30s jittered
   delays. Parallel Maps requests will get the operator IP-banned within minutes.
4. **Never silently swallow exceptions.** Every failure surfaces in the UI as
   a status pill and (if possible) an error message.
5. **Never break idempotency.** Running the same Maps URL twice must not
   produce duplicate output.
6. **Never invent libraries.** Stick to what's in `requirements.txt`. If you
   need a new dep, add it explicitly with a one-line justification.
7. **Never edit `__pycache__/`, `.venv/`, `node_modules/`, generated CSVs.**

## Soft rules (defaults you can break with a reason)

- Prefer `async def` over `def` in scrapers — they all live in the event loop.
- Prefer Pydantic models over `dict` at HTTP boundaries.
- Prefer functions over classes (use classes only for Pydantic / ORM / config).
- Prefer Roman-Urdu comments in `scrape/` (operator's style) and English in
  `lead-scraper/` (production layer).
- Keep selectors at the top of each scraper module, dated. They rot.

## Workflow

When the operator asks for a change:

1. **Read the relevant code first.** Do not propose an architecture before
   you know what's there. CLAUDE.md has a "Where to start" table.
2. **Update specs in the same commit.** If you change behavior, update
   `specs/specs.md` and `specs/tasks.md`. A stale spec is worse than no spec.
3. **Run the smoke test.** `uvicorn app.main:app` should start clean and
   `GET /healthz` should return `{"ok": true}`.
4. **Test against a real Maps URL.** Mocks lie. The whole project is built
   on the assumption that Google's DOM is fragile — test on the real thing.
5. **Communicate failures.** If a selector breaks, surface the diff in the
   response, don't return empty data.

## What the operator cares about (in order)

1. The thing runs. The UI opens, the scrapers complete, the CSV downloads.
2. The thing is honest. A confidence-low match is shown as low. A missed field
   is shown as `—`, not a fabricated value.
3. The thing is fast enough. Sequential is fine for Maps. Parallel is fine for
   websites. Don't over-engineer for scale the operator will never hit.
4. The thing looks good. The operator stares at this UI every day.

## What the operator does NOT care about (in order)

1. Microservices, Docker, Kubernetes.
2. Multi-tenancy, auth, billing.
3. Type-checker purity at the expense of readability.
4. A clever abstraction that saves 5 lines but takes 30 minutes to understand.

## When you finish a task

- Update `specs/tasks.md` checkbox to `[x]` if you closed a task.
- Add a one-line entry to `CHANGELOG.md` if it exists.
- Do not commit if the smoke test fails. Tell the operator.

## Recovery

If you broke something:

1. `git status` — see what changed.
2. `git diff` — look at it before reverting blindly.
3. The frontend has no build step — refresh the tab to see new state.
4. The backend has `--reload` in `run.sh` — uvicorn restarts on save.

The operator will trust you more if you tell them what broke than if you try
to silently patch it.
