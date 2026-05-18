#!/usr/bin/env bash
# Stop local dev servers (backend 3001, frontend 5173).

set -euo pipefail

kill_port() {
  local port=$1
  local pids
  pids=$(lsof -ti:"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "Stopping port $port (PID: $pids)"
    # shellcheck disable=SC2086
    kill -9 $pids 2>/dev/null || true
  fi
}

kill_port 3001
kill_port 5173
echo "Dev servers stopped."
