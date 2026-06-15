#!/usr/bin/env bash
# Download Noto Sans CJK SC for matplotlib charts (optional; ~16MB).
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)/fonts"
FILE="$DIR/NotoSansCJKsc-Regular.otf"
mkdir -p "$DIR"
if [ -s "$FILE" ]; then
  echo "OK: $FILE"
  exit 0
fi
curl -fsSL --retry 2 -L -o "$FILE" \
  "https://cdn.jsdelivr.net/gh/notofonts/noto-cjk@main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
echo "Downloaded: $FILE"
