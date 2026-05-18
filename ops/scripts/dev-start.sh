#!/usr/bin/env bash
# Start backend + frontend for local development.
# Always frees port 3001 first so `make dev` reliably restarts the API.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BACKEND_PORT="${MCHAT_BACKEND_PORT:-3001}"
FRONTEND_PORT="${MCHAT_FRONTEND_PORT:-5173}"

kill_port() {
  local port=$1
  local pids
  pids=$(lsof -ti:"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "→ Freeing port $port (was PID: $pids)"
    # shellcheck disable=SC2086
    kill -9 $pids 2>/dev/null || true
    sleep 0.3
  fi
}

kill_port "$BACKEND_PORT"
# Vite binds 5173; kill so `make dev` can restart frontend too
kill_port "$FRONTEND_PORT"

cd "$ROOT/src/backend"
if [ ! -d venv ]; then
  echo "Missing venv. Run: make install"
  exit 1
fi
# shellcheck disable=SC1091
source venv/bin/activate

echo "→ Starting backend http://127.0.0.1:${BACKEND_PORT}"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf "http://127.0.0.1:${BACKEND_PORT}/docs" -o /dev/null 2>/dev/null; then
    echo "→ Backend ready (PID $BACKEND_PID)"
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Backend exited. Check errors above."
    exit 1
  fi
  if [ "$i" -eq 10 ]; then
    echo "Backend did not respond in time (still starting? PID $BACKEND_PID)"
  fi
  sleep 0.5
done

cd "$ROOT/src/frontend"
echo "→ Starting frontend http://127.0.0.1:${FRONTEND_PORT}"
echo "  Login: admin / admin123 (or your .env ADMIN_* values)"
exec npm run dev
