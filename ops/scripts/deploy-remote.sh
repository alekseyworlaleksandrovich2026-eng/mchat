#!/bin/bash
# Deploy mchat to remote server
# Usage: bash ops/scripts/deploy-remote.sh [user@host]
set -euo pipefail

REMOTE="${1:-xiaoxiao@10.98.8.15}"
REMOTE_DIR="/opt/xiaoxiao/mchat"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "==> Build frontend (local)"
cd "$PROJECT_DIR/src/frontend"
npm run build

echo "==> Generate production .env"
JWT_SECRET=$(openssl rand -hex 32)
ENV_FILE="$PROJECT_DIR/ops/deploy/.env.production.generated"
cat > "$ENV_FILE" <<EOF
DATABASE_URL=mysql+aiomysql://mchat:112358xx@10.98.8.8:3306/mchat
REDIS_URL=redis://10.98.8.12:6379/0

JWT_SECRET=${JWT_SECRET}
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

echo "==> Rsync to ${REMOTE}:${REMOTE_DIR}"
rsync -avz --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'src/frontend/node_modules' \
  --exclude 'src/backend/venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'src/backend/logs' \
  --exclude 'src/frontend/.vite' \
  "$PROJECT_DIR/" "${REMOTE}:${REMOTE_DIR}/"

rsync -avz "$ENV_FILE" "${REMOTE}:${REMOTE_DIR}/.env"

echo "==> Fix frontend dist permissions on server"
ssh "$REMOTE" "chmod -R a+rX ${REMOTE_DIR}/src/frontend/dist 2>/dev/null || true"

echo "==> Remote setup"
ssh "$REMOTE" "chmod +x ${REMOTE_DIR}/ops/deploy/remote-setup.sh && bash ${REMOTE_DIR}/ops/deploy/remote-setup.sh"

echo ""
echo "Deployed to http://10.98.8.15:5180/admin"
echo "Admin: admin / admin123 (change after login)"
echo "JWT_SECRET saved in ops/deploy/.env.production.generated (local only)"
