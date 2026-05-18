#!/bin/bash
# Install mchat.9235.net nginx vhost on 10.98.8.12 (requires sudo password on that host)
set -euo pipefail

NGINX_HOST="${NGINX_HOST:-xiaoxiao@10.98.8.12}"
NGINX_PORT="${NGINX_PORT:-5566}"
CONF_NAME="mchat.9235.net.conf"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "==> Upload ${CONF_NAME}"
scp -P "$NGINX_PORT" "$PROJECT_DIR/ops/deploy/${CONF_NAME}" "${NGINX_HOST}:/tmp/${CONF_NAME}"

echo "==> Install & reload nginx (sudo)"
ssh -t -p "$NGINX_PORT" "$NGINX_HOST" "sudo cp /tmp/${CONF_NAME} /etc/nginx/conf.d/${CONF_NAME} && sudo nginx -t && sudo systemctl reload nginx && echo '✅ https://mchat.9235.net ready'"

echo ""
echo "Verify: curl -sI https://mchat.9235.net/admin"
