#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ -d ".venv" ]; then
  if [ -f ".venv/bin/activate" ]; then
    # macOS / Linux
    source ".venv/bin/activate"
  elif [ -f ".venv/Scripts/activate" ]; then
    # Windows (Git Bash)
    source ".venv/Scripts/activate"
  fi
fi

if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8000}"

# server.py installs the WindowsProactorEventLoopPolicy before uvicorn boots,
# which is required for Playwright on Windows. Harmless on macOS / Linux.
exec python server.py
