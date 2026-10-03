#!/usr/bin/env bash
# Mirror origin/main; if it moved (or with --force), refresh the server venv,
# rebuild the search corpus, restart, and health-check. No-op otherwise.
set -euo pipefail

APP_DIR=/opt/scholarboard
APP_USER=scholarboard
DATA_DIR=/var/lib/scholarboard

cd "$APP_DIR"
before="$(git rev-parse HEAD)"
git fetch --quiet origin main
git reset --quiet --hard origin/main
[[ "$before" != "$(git rev-parse HEAD)" || "${1:-}" == "--force" ]] || exit 0
echo "Updating $before → $(git rev-parse HEAD)"

uv pip install --quiet --python "$APP_DIR/.venv-server/bin/python" -r server/requirements.txt
sudo -u "$APP_USER" env PYTHONPATH="$APP_DIR" "$APP_DIR/.venv-server/bin/python" \
  -m scholar_board.nlsearch.corpus --out "$DATA_DIR/corpus"
systemctl restart scholarboard

for _ in $(seq 1 20); do
  curl --fail --silent http://127.0.0.1:8001/api/health >/dev/null && { echo "Healthy."; exit 0; }
  sleep 1
done
echo "Health check failed." >&2
exit 1
