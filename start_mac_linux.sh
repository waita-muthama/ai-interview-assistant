#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -f ".venv/bin/python" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi
if [ ! -f ".env" ]; then
  cp .env.example .env
  chmod 600 .env
fi
# Prompts only when no API key is configured and a terminal is attached.
.venv/bin/python setup_api_key.py
if ! .venv/bin/python -c 'import fastapi, uvicorn, httpx, dotenv, docx, pypdf, multipart' >/dev/null 2>&1; then
  .venv/bin/python -m pip install -r requirements.txt
fi
echo "Open http://127.0.0.1:8765 in Chrome or Edge. Press Ctrl+C to stop."
exec .venv/bin/python -m uvicorn server.main:app --host 127.0.0.1 --port 8765
