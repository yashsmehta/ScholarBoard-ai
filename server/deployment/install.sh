#!/usr/bin/env bash
# Install the ScholarBoard AI-search API on a server that also hosts other apps
# (aos-ai). Idempotent: safe to re-run. Touches only ScholarBoard's own user,
# paths, unit files, and Caddy site block.
set -euo pipefail

APP_DIR=/opt/scholarboard
APP_USER=scholarboard
DATA_DIR=/var/lib/scholarboard
PORT=8001
DOMAIN="${1:-scholarboard.yashsmehta.com}"

[[ "${EUID}" -eq 0 ]] || { echo "Run this script as root." >&2; exit 1; }
[[ "$(cd "$(dirname "$0")/../.." && pwd)" == "$APP_DIR" ]] || { echo "Clone the repository to $APP_DIR first." >&2; exit 1; }
for bin in uv caddy git curl; do
  command -v "$bin" >/dev/null || { echo "Missing $bin." >&2; exit 1; }
done

# Antigravity CLI (Google's installer verifies the SHA-512 of the download).
if ! command -v agy >/dev/null; then
  curl -fsSL https://antigravity.google/cli/install.sh | bash -s -- --dir /usr/local/bin
fi

# Claude Code (optional engine; subscription sign-in is a manual step, see README).
command -v claude >/dev/null || npm install --global @anthropic-ai/claude-code

id "$APP_USER" >/dev/null 2>&1 || useradd --system --create-home --home-dir "$DATA_DIR" --shell /usr/sbin/nologin "$APP_USER"
install -d -o "$APP_USER" -g "$APP_USER" -m 750 "$DATA_DIR"

if [[ ! -f "$APP_DIR/.env" ]]; then
  install -o root -g "$APP_USER" -m 640 "$APP_DIR/server/deployment/env.example" "$APP_DIR/.env"
  echo "Created $APP_DIR/.env — set GEMINI_API_KEY there."
fi
chown root:"$APP_USER" "$APP_DIR/.env"
chmod 640 "$APP_DIR/.env"

uv venv --allow-existing "$APP_DIR/.venv-server"
uv pip install --python "$APP_DIR/.venv-server/bin/python" -r "$APP_DIR/server/requirements.txt"
sudo -u "$APP_USER" env PYTHONPATH="$APP_DIR" "$APP_DIR/.venv-server/bin/python" \
  -m scholar_board.nlsearch.corpus --out "$DATA_DIR/corpus"

# The search agent runs with all tool permissions, so the service is sandboxed:
# read-only OS, writable only in $DATA_DIR, no view of aos-ai or other homes.
install -m 644 /dev/stdin /etc/systemd/system/scholarboard.service <<EOF
[Unit]
Description=ScholarBoard AI-search API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=HOME=$DATA_DIR
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$APP_DIR
Environment=NL_SEARCH_CORPUS_DIR=$DATA_DIR/corpus
Environment=NL_SEARCH_DATA_DIR=$DATA_DIR
Environment=NL_SEARCH_AGY_HOME=$DATA_DIR/agy-home
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv-server/bin/uvicorn server.app:app --host 127.0.0.1 --port $PORT --workers 1 --proxy-headers
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR
InaccessiblePaths=-/opt/aos-ai -/var/lib/aos-ai -/etc/caddy -/var/lib/caddy -/root
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
CapabilityBoundingSet=
# Leave headroom for aos-ai on the shared box.
MemoryMax=2G
CPUWeight=50

[Install]
WantedBy=multi-user.target
EOF

# Mirror GitHub every 30 min; update.sh is a no-op when nothing changed.
install -m 644 /dev/stdin /etc/systemd/system/scholarboard-update.service <<EOF
[Unit]
Description=Update ScholarBoard AI search from GitHub

[Service]
Type=oneshot
ExecStart=$APP_DIR/server/deployment/update.sh
EOF
install -m 644 /dev/stdin /etc/systemd/system/scholarboard-update.timer <<'EOF'
[Unit]
Description=Periodic ScholarBoard AI-search update

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target
EOF

# Public Caddy site block (no basic_auth). Appended once; other sites untouched.
if ! grep -q "^$DOMAIN {" /etc/caddy/Caddyfile; then
  cp /etc/caddy/Caddyfile "/etc/caddy/Caddyfile.bak.$(date +%s)"
  cat >> /etc/caddy/Caddyfile <<EOF

$DOMAIN {
	encode zstd gzip
	request_body {
		max_size 64KB
	}
	reverse_proxy 127.0.0.1:$PORT
}
EOF
fi
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

chmod 755 "$APP_DIR/server/deployment/"*.sh
systemctl daemon-reload
systemctl enable --now scholarboard.service scholarboard-update.timer
systemctl restart scholarboard.service
systemctl reload caddy
echo "Installed. Health: curl http://127.0.0.1:$PORT/api/health"
