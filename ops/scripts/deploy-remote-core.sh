#!/bin/bash
# Deploy mchat Core (standalone vertical RAG, no Cloud features) to remote server.
# Usage: bash ops/scripts/deploy-remote-core.sh
set -euo pipefail

REMOTE="${1:-xiaoxiao@192.169.177.210}"
REMOTE_DIR="/opt/xiaoxiao/mchat"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "==> Build frontend (Core edition)"
cd "$PROJECT_DIR/src/frontend"
VITE_MCHAT_EDITION=core npm run build:core

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

# Preserve existing server .env; only bootstrap if missing
if ssh "$REMOTE" "test -f ${REMOTE_DIR}/.env"; then
  echo "==> Keep existing ${REMOTE_DIR}/.env on server"
else
  echo "==> Create initial .env on server"
  JWT_SECRET=$(openssl rand -hex 32)
  ENV_FILE="$PROJECT_DIR/ops/deploy/.env.production.generated"
  cat > "$ENV_FILE" <<'EOF'
DATABASE_URL=mysql+aiomysql://mchat:112358xx@127.0.0.1:3306/mchat

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
  echo "==> Sync skills/mchat-help"
  ssh "$REMOTE" "mkdir -p ${REMOTE_DIR}/skills/mchat-help"
  rsync -avz \
    "$PROJECT_DIR/skills/mchat-help/" \
    "${REMOTE}:${REMOTE_DIR}/skills/mchat-help/"
fi

echo "==> Remote setup (Core backend: app.main:app)"
ssh "$REMOTE" "chmod +x ${REMOTE_DIR}/ops/deploy/remote-setup.sh && bash ${REMOTE_DIR}/ops/deploy/remote-setup.sh"

echo ""
echo "Core deployed to http://mchat.chat"
echo "  Admin:  http://mchat.chat/admin"
echo "  API:    http://mchat.chat/docs"
