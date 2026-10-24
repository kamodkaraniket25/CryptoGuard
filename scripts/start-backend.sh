#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
fi
exec python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
