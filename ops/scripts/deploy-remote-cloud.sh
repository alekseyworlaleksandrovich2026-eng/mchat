#!/bin/bash
# Deploy mchat Cloud (Core + signup/portal/templates) to remote server.
# Usage: bash ops/scripts/deploy-remote-cloud.sh
set -euo pipefail

REMOTE="${1:-xiaoxiao@10.98.8.15}"
REMOTE_DIR="/opt/xiaoxiao/mchat"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "==> Build frontend (local)"
cd "$PROJECT_DIR/src/frontend"
npm run build

echo "==> Rsync to ${REMOTE}:${REMOTE_DIR}"
rsync -avz --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'src/frontend/node_modules' \
  --exclude 'src/backend/venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'ops/deploy/.env.production.generated' \
  --exclude 'src/backend/logs' \
  --exclude 'logs' \
  --exclude 'skills' \
  --exclude 'data' \
  --exclude 'uploads' \
  --exclude 'test.db' \
  --exclude '.pytest_cache' \
  --exclude 'src/frontend/.vite' \
  "$PROJECT_DIR/" "${REMOTE}:${REMOTE_DIR}/"

# Preserve existing server .env (JWT, passwords); only bootstrap if missing
if ssh "$REMOTE" "test -f ${REMOTE_DIR}/.env"; then
  echo "==> Keep existing ${REMOTE_DIR}/.env on server"
else
  echo "==> Create initial .env on server"
  JWT_SECRET=$(openssl rand -hex 32)
  ENV_FILE="$PROJECT_DIR/ops/deploy/.env.production.generated"
  cat > "$ENV_FILE" <<'EOF'
DATABASE_URL=mysql+aiomysql://mchat:112358xx@10.98.8.8:3306/mchat
REDIS_URL=redis://10.98.8.12:6379/0

JWT_SECRET=__JWT_SECRET__
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

SERVER_HOST=0.0.0.0
SERVER_PORT=3001

MILVUS_ENABLED=false
MILVUS_HOST=localhost
MILVUS_PORT=19530

SKILLS_DIR=/opt/xiaoxiao/mchat/skills
UPLOAD_DIR=/opt/xiaoxiao/mchat/data/uploads
MAX_UPLOAD_SIZE_MB=50

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EOF
  sed -i '' "s/__JWT_SECRET__/${JWT_SECRET}/g" "$ENV_FILE"
  rsync -avz "$ENV_FILE" "${REMOTE}:${REMOTE_DIR}/.env"
fi

echo "==> Fix frontend dist permissions on server"
ssh "$REMOTE" "chmod -R a+rX ${REMOTE_DIR}/src/frontend/dist 2>/dev/null || true"

if [ -d "$PROJECT_DIR/skills/mchat-help" ]; then
  echo "==> Sync skills/mchat-help (other server skills untouched)"
  ssh "$REMOTE" "mkdir -p ${REMOTE_DIR}/skills/mchat-help"
  rsync -avz \
    "$PROJECT_DIR/skills/mchat-help/" \
    "${REMOTE}:${REMOTE_DIR}/skills/mchat-help/"
fi

echo "==> Remote setup (pip, db migrate, restart Cloud services)"
ssh "$REMOTE" "chmod +x ${REMOTE_DIR}/ops/deploy/remote-setup-cloud.sh && bash ${REMOTE_DIR}/ops/deploy/remote-setup-cloud.sh"

echo ""
echo "Cloud deployed to https://mchat.9235.net"
echo "  Admin:    https://mchat.9235.net/admin"
echo "  Portal:   https://mchat.9235.net/portal"
echo "  API docs: https://mchat.9235.net/docs"
echo "  Register: https://mchat.9235.net/register"
