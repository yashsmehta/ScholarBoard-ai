#!/usr/bin/env bash
set -euo pipefail

# Deploy ScholarBoard.ai as a static site to the Jekyll repo's scholarboard/ directory.
# Usage: bash scripts/deploy_static.sh [JEKYLL_SITE_DIR]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DATA_DIR="$PROJECT_ROOT/data/build"

# Jekyll site location (default or argument)
JEKYLL_DIR="${1:-$HOME/Websites/yashsmehta.github.io}"
DEST="$JEKYLL_DIR/scholarboard"

if [ ! -d "$JEKYLL_DIR" ]; then
  echo "Error: Jekyll site not found at $JEKYLL_DIR"
  echo "Usage: bash scripts/deploy_static.sh /path/to/jekyll/site"
  exit 1
fi

echo "=== Building frontend with base=/scholarboard/ ==="
cd "$FRONTEND_DIR"
VITE_BASE=/scholarboard/ npm run build

echo ""
echo "=== Copying data files into dist/ ==="
mkdir -p "$FRONTEND_DIR/dist/data/build/profile_pics"

cp "$DATA_DIR/scholars.json" "$FRONTEND_DIR/dist/data/build/scholars.json"
echo "  scholars.json ($(du -h "$DATA_DIR/scholars.json" | cut -f1))"

if [ -f "$DATA_DIR/field_directions.json" ]; then
  cp "$DATA_DIR/field_directions.json" "$FRONTEND_DIR/dist/data/build/field_directions.json"
  echo "  field_directions.json ($(du -h "$DATA_DIR/field_directions.json" | cut -f1))"
fi

if [ -d "$DATA_DIR/profile_pics" ]; then
  cp -r "$DATA_DIR/profile_pics/"* "$FRONTEND_DIR/dist/data/build/profile_pics/"
  PIC_COUNT=$(ls "$DATA_DIR/profile_pics/" | wc -l | tr -d ' ')
  echo "  profile_pics/ ($PIC_COUNT files)"
fi

echo ""
echo "=== Syncing to $DEST ==="
rm -rf "$DEST"
cp -r "$FRONTEND_DIR/dist" "$DEST"

TOTAL_SIZE=$(du -sh "$DEST" | cut -f1)
echo "  Total size: $TOTAL_SIZE"

echo ""
echo "=== Done! ==="
echo ""
echo "Next steps:"
echo "  cd $JEKYLL_DIR"
echo "  git add scholarboard/"
echo "  git commit -m 'Add ScholarBoard.ai static app'"
echo "  # Then deploy with bin/deploy or push to trigger GitHub Pages"
