# AI Search server

The natural-language search API (`server/app.py`) runs on the aos-ai box
(`ssh aos-prod`) next to Art of Shaadi, fully separate from it:

| | |
|---|---|
| Public URL | `https://scholarboard.yashsmehta.com` (Caddy, auto-HTTPS; DNS: Namecheap A record → server IP) |
| Code | `/opt/scholarboard` (clone of `main`; `.env` is `640 root:scholarboard`) |
| Data | `/var/lib/scholarboard` — `corpus/`, `agy-home/`, `searches.jsonl` |
| Service | `scholarboard.service` → uvicorn on `127.0.0.1:8001`, user `scholarboard` |
| Agent | `/usr/local/bin/agy` (Antigravity CLI), Gemini API key auth |

The agent runs with every tool permission auto-approved, so the unit is
sandboxed: read-only OS, writable only in `/var/lib/scholarboard`, and
`/opt/aos-ai`, `/var/lib/aos-ai`, `/etc/caddy`, `/root`, `/home` are invisible.

## Install / update

```bash
git clone https://github.com/yashsmehta/ScholarBoard-ai.git /opt/scholarboard
cd /opt/scholarboard && ./server/deployment/install.sh   # then set GEMINI_API_KEY in .env
```

`scholarboard-update.timer` runs `update.sh` every 30 min: it mirrors
`origin/main`, and when it moved, rebuilds the corpus and restarts.
Force one with `/opt/scholarboard/server/deployment/update.sh --force`.

## Claude Code engine (optional)

Search can also run on headless Claude Code (Sonnet, medium effort, read-only
tools), billed to a Claude **subscription**, never the API. To enable it:

```bash
sudo -u scholarboard -H env HOME=/var/lib/scholarboard claude setup-token
# put the printed token in /opt/scholarboard/.env as CLAUDE_CODE_OAUTH_TOKEN=...
# and set NL_SEARCH_ENGINES=agy,claude, then:
systemctl restart scholarboard
```

The site then shows a quiet Antigravity / Claude Code choice under the search
box (Antigravity stays the default).

## Operations

```bash
systemctl status scholarboard
journalctl -u scholarboard -f
curl -s localhost:8001/api/health
tail /var/lib/scholarboard/searches.jsonl     # query, seconds, result ids
```

Settings live in `/opt/scholarboard/.env` (see `env.example`); restart after
editing. Measured on this 2-CPU / 4 GB box: one search ≈ 50 s, ~140 MB and
~5 CPU-s; 10 concurrent searches finished in 48–110 s with 1.4 GB peak memory
and no impact on aos-ai. Cost ≈ $0.21 per uncached search with
`gemini-3.8-flash` ($0.75/M input, $0.075/M cached, $3.75/M output).
