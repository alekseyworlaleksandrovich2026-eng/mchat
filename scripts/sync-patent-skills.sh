#!/usr/bin/env bash
# 从 patents 源仓库同步到 mchat/skills
set -euo pipefail
SRC="${1:-/Users/xiaoxiao/dev/skills/patents}"
DST="${2:-/Users/xiaoxiao/dev/mchat/skills}"
RSYNC_EXCLUDE=(--exclude 'config.json' --exclude 'dist/' --exclude '__pycache__/' --exclude '.git/')

rsync -a "${RSYNC_EXCLUDE[@]}" "$SRC/patent-search/" "$DST/patent-search/"
rsync -a "${RSYNC_EXCLUDE[@]}" "$SRC/patent-transaction/" "$DST/patent-transaction/"
rsync -a "${RSYNC_EXCLUDE[@]}" "$SRC/patent-disclosure/" "$DST/patent-disclosure/"

echo "✅ 已同步到 $DST"
echo "   重启 mchat 后端或执行: cd src/backend && <venv-python> ../../scripts/reload-patent-skills.py"
