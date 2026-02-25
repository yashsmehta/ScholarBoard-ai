"""
Data server for ScholarBoard.ai frontend.

Serves scholar data, profile pics, and API endpoints.
The React frontend (Vite dev server) proxies /api and /data to this server.

Usage:
    .venv/bin/python3 serve.py              # http://localhost:8000
    .venv/bin/python3 serve.py --port 9000  # custom port
"""

import http.server
import socketserver
import json
import sys
import os
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

sys.path.insert(0, str(PROJECT_ROOT))


class ScholarHandler(http.server.SimpleHTTPRequestHandler):
    """Serves /data/ static files and /api/ endpoints."""

    def do_GET(self):
        if self.path == "/api/scholars":
            self.serve_scholars()
        elif self.path.startswith("/api/scholar/"):
            scholar_id = self.path.split("/")[-1]
            self.serve_scholar(scholar_id)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/search":
            self.handle_search()
        else:
            self.send_error(404, "Not Found")

    def serve_scholars(self):
        """Serve the full scholars.json."""
        path = DATA_DIR / "scholars.json"
        if not path.exists():
            self.send_error(404, "scholars.json not found")
            return
        self._send_json(path.read_text(encoding="utf-8"))

    def serve_scholar(self, scholar_id):
        """Serve a single scholar by ID."""
        path = DATA_DIR / "scholars.json"
        if not path.exists():
            self.send_error(404, "scholars.json not found")
            return

        scholars = json.loads(path.read_text(encoding="utf-8"))
        scholar = scholars.get(scholar_id)

        # Try zero-padded ID
        if not scholar and scholar_id.isdigit():
            scholar = scholars.get(scholar_id.zfill(4))

        if not scholar:
            self.send_error(404, f"Scholar {scholar_id} not found")
            return

        self._send_json(json.dumps(scholar))

    def handle_search(self):
        """Handle POST search requests (name or research query)."""
        try:
            body = self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8")
            request = json.loads(body)
        except (ValueError, KeyError):
            self.send_error(400, "Invalid request")
            return

        query = request.get("query", "")
        search_type = request.get("type", "name")
        if not query:
            self.send_error(400, "Missing query")
            return

        path = DATA_DIR / "scholars.json"
        if not path.exists():
            self.send_error(404, "scholars.json not found")
            return

        scholars = json.loads(path.read_text(encoding="utf-8"))

        if search_type == "name":
            query_lower = query.lower()
            results = [
                {
                    "id": sid,
                    "name": s.get("name", ""),
                    "institution": s.get("institution", ""),
                    "umap": [
                        s.get("umap_projection", {}).get("x", 0),
                        s.get("umap_projection", {}).get("y", 0),
                    ],
                }
                for sid, s in scholars.items()
                if query_lower in s.get("name", "").lower()
            ]
            results.sort(key=lambda r: 0 if r["name"].lower() == query_lower else 1)
            self._send_json(json.dumps({"type": "name", "results": results[:10]}))

        elif search_type == "research":
            try:
                from scholar_board.search_embeddings import get_query_umap_coords

                result = get_query_umap_coords(query)
                if result["error"]:
                    self.send_error(500, f"Projection error: {result['error']}")
                    return
                x, y = result["coords"]
                self._send_json(json.dumps({"type": "research", "coords": [float(x), float(y)]}))
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(400, f"Unknown search type: {search_type}")

    def _send_json(self, body: str):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)


def main():
    parser = argparse.ArgumentParser(description="ScholarBoard.ai data server")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # Serve static files from project root so /data/* resolves to data/*
    os.chdir(PROJECT_ROOT)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", args.port), ScholarHandler) as httpd:
        print(f"Serving at http://localhost:{args.port}")
        print(f"Data directory: {DATA_DIR}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
