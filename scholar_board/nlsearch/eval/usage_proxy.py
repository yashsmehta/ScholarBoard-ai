"""Logging reverse proxy for the Gemini API: forwards everything to Google and
appends each response's usageMetadata (one line per model call) to $USAGE_LOG.
Point a client at http://127.0.0.1:8765/run/<tag> to tag its calls (so
parallel runs can be told apart); the prefix is stripped before forwarding.

Run: USAGE_LOG=... uv run --with httpx --with starlette --with uvicorn uvicorn usage_proxy:app --port 8765
"""
import json
import os
import re
import time

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

UPSTREAM = "https://generativelanguage.googleapis.com"
client = httpx.AsyncClient(timeout=600)


async def proxy(request: Request) -> Response:
    tag, path = None, request.url.path
    if m := re.match(r"/run/([^/]+)(/.*)", path):
        tag, path = m.group(1), m.group(2)
    url = UPSTREAM + path + (("?" + request.url.query) if request.url.query else "")
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length", "accept-encoding")}
    t0 = time.time()
    r = await client.request(request.method, url, headers=headers, content=await request.body())
    body = r.content
    usages = [json.loads(m) for m in re.findall(rb'"usageMetadata":\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', body)]
    if usages:
        with open(os.environ["USAGE_LOG"], "a") as f:
            f.write(json.dumps({"path": path, "tag": tag, "usage": usages[-1], "start": round(t0, 2),
                                "seconds": round(time.time() - t0, 2)}) + "\n")
    out_headers = {k: v for k, v in r.headers.items() if k.lower() not in ("content-length", "content-encoding", "transfer-encoding", "connection")}
    return Response(body, status_code=r.status_code, headers=out_headers)


app = Starlette(routes=[Route("/{path:path}", proxy, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])])
