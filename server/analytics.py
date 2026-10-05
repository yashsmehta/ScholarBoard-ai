"""Visitor analytics for the search log: salted-hash visitor id, offline geo lookup, device class.

The raw IP is never written anywhere. A visitor is `sha256(salt + ip)[:12]` (salt is a random
secret in DATA_DIR/visitor_salt), geography comes from an offline DB-IP City Lite database in
DATA_DIR/geo/dbip-city-lite.mmdb (no IP leaves the server; missing DB → no geo).
"""

import hashlib
import ipaddress
import logging
import os
import re
import secrets
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger("scholarboard.analytics")

GEO_DB = "geo/dbip-city-lite.mmdb"
_salt: bytes | None = None
_reader = None
_reader_tried = False


def _get_salt(data_dir: Path) -> bytes:
    global _salt
    if _salt is None:
        path = data_dir / "visitor_salt"
        try:
            _salt = path.read_bytes()
        except OSError:
            _salt = secrets.token_bytes(32)
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as f:
                    f.write(_salt)
            except OSError as err:
                logger.warning("could not persist visitor salt: %s", err)
    return _salt


def visitor_id(ip: str, data_dir: Path) -> str:
    return hashlib.sha256(_get_salt(data_dir) + ip.encode()).hexdigest()[:12]


@lru_cache(maxsize=2048)
def _geo(ip: str, db_path: str) -> dict:
    global _reader, _reader_tried
    if not _reader_tried:
        _reader_tried = True
        try:
            import maxminddb
            _reader = maxminddb.open_database(db_path)
        except Exception as err:  # missing DB or package: log without geo
            logger.warning("geo lookup disabled: %s", err)
    if _reader is None:
        return {}
    try:
        if not ipaddress.ip_address(ip).is_global:
            return {}
        rec = _reader.get(ip) or {}
    except Exception:
        return {}
    name = lambda d: (d or {}).get("names", {}).get("en")
    sub = (rec.get("subdivisions") or [None])[0]
    out = {"country": (rec.get("country") or {}).get("iso_code"), "region": name(sub), "city": name(rec.get("city"))}
    return {k: v for k, v in out.items() if v}


def geo(ip: str, data_dir: Path) -> dict:
    return _geo(ip, str(data_dir / GEO_DB))


def device(user_agent: str) -> str:
    ua = (user_agent or "").lower()
    if re.search(r"bot|crawl|spider|curl|python-requests|httpx|wget", ua):
        return "bot"
    if re.search(r"mobi|android|iphone|ipad", ua):
        return "mobile"
    return "desktop" if ua else "unknown"


def visitor_info(ip: str, headers, data_dir: Path) -> dict:
    """Fields merged into every log entry for one request."""
    ref = urlparse(headers.get("origin") or headers.get("referer") or "").netloc
    info = {"visitor": visitor_id(ip, data_dir), **geo(ip, data_dir),
            "device": device(headers.get("user-agent", ""))}
    if ref:
        info["referrer"] = ref
    return info
