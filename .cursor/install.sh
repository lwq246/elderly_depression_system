#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the elderly depression screening stack.
# Prepares the Python backend (FastAPI) and the Next.js frontend.
set -euo pipefail

cd "$(dirname "$0")/.."

# The Cursor base image ships Python 3.12 but not the venv/ensurepip module.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y --no-install-recommends python3.12-venv
fi

# Backend: isolated virtualenv + pinned requirements.
python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

# Runtime config: OPENAI_API_KEY is injected as a secret env var and takes
# precedence over the (empty) value in this file, which only carries defaults.
[ -f .env ] || cp .env.example .env

# Frontend: deterministic install from the committed lockfile.
( cd frontend && npm ci )
