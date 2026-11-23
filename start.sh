#!/usr/bin/env bash
# Starts the ContextShield backend and frontend together (macOS/Linux).
# Windows users: start.bat. Stop both with Ctrl+C.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x backend/.venv/bin/python ]; then
  echo "backend/.venv is missing. Set it up first (see README, section 5):"
  echo "  cd backend && python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt"
  exit 1
fi
if [ ! -d frontend/node_modules ]; then
  echo "frontend/node_modules is missing. Run: cd frontend && npm install"
  exit 1
fi

(cd backend && exec .venv/bin/python -m uvicorn app.main:app --port 8000) &
backend=$!
(cd frontend && exec npm run dev) &
frontend=$!
# On Ctrl+C, or when either server exits, stop everything this script started.
trap 'trap - EXIT INT TERM; kill 0 2>/dev/null || true' EXIT INT TERM

echo "Backend:  http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
wait -n "$backend" "$frontend"
