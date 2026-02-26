"""
Download scholar profile pictures using Serper.dev Google Image Search API.

Uses image search with face-related queries to find headshot photos.
Falls back gracefully when no suitable image is found.

Usage:
    uv run -m scholar_board.pipeline.pics --dry-run
    uv run -m scholar_board.pipeline.pics --skip-existing
    uv run -m scholar_board.pipeline.pics --limit 10
"""

import argparse
import hashlib
import time
from io import BytesIO

import requests
from PIL import Image

from scholar_board.config import PICS_DIR, get_serper_api_key
from scholar_board.db import get_connection, init_db, ensure_scholar, upsert_profile_pic, load_scholars

DEFAULT_AVATAR = PICS_DIR / "default_avatar.jpg"
SERPER_URL = "https://google.serper.dev/images"
MAX_DIM = 400
JPEG_QUALITY = 70


def pic_filename(name: str, scholar_id: str) -> str:
    return f"{name.replace(' ', '_').lower()}_{scholar_id}.jpg"


def file_md5(path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def needs_photo(scholar: dict, default_md5: str) -> bool:
    """Check if scholar needs a new photo (missing or is default avatar)."""
    path = PICS_DIR / pic_filename(scholar["scholar_name"], scholar["scholar_id"])
    if not path.exists():
        return True
    return file_md5(path) == default_md5


def search_face_images(name: str, institution: str, api_key: str, num: int = 10) -> list[str]:
    """Search for face images using Serper.dev image search."""
    query = f"{name} {institution} neuroscience researcher headshot"
    resp = requests.post(
        SERPER_URL,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": num},
        timeout=15,
    )
    resp.raise_for_status()
    return [
        img["imageUrl"]
        for img in resp.json().get("images", [])
        if img["imageUrl"].startswith("http")
    ]


def download_and_save(url: str, output_path) -> bool:
    """Download image, validate as headshot, resize, and save as JPEG."""
    resp = requests.get(
        url,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ScholarBoard/1.0)"},
    )
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content)).convert("RGB")
    w, h = img.size
    if w < 80 or h < 80:
        raise ValueError(f"Too small ({w}x{h})")
    if w > h * 1.4:
        raise ValueError(f"Too landscape ({w}x{h})")
    if max(img.size) > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM))
    img.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    return True


def main():
    parser = argparse.ArgumentParser(description="Download scholar profile pictures")
    parser.add_argument("--dry-run", action="store_true", help="Preview without downloading")
    parser.add_argument("--limit", type=int, default=0, help="Max scholars to process")
    parser.add_argument("--test", action="store_true", help="Test with a single known scholar")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Only download for scholars with default avatar")
    args = parser.parse_args()

    api_key = get_serper_api_key()
    if not api_key:
        print("Error: Set SERPER_API_KEY in .env")
        return

    PICS_DIR.mkdir(parents=True, exist_ok=True)

    if args.test:
        print("Testing with Michael Bonner (Johns Hopkins)...")
        urls = search_face_images("Michael Bonner", "Johns Hopkins University", api_key)
        if urls:
            print(f"  Found {len(urls)} images:")
            for url in urls:
                print(f"    {url}")
            test_path = PICS_DIR / "test_michael_bonner.jpg"
            if download_and_save(urls[0], test_path):
                print(f"  Saved test image to {test_path}")
        else:
            print("  No images found — check your API key")
        return

    scholars = load_scholars(is_pi_only=True)
    default_md5 = file_md5(DEFAULT_AVATAR) if DEFAULT_AVATAR.exists() else ""

    if args.skip_existing:
        todo = [s for s in scholars if needs_photo(s, default_md5)]
    else:
        todo = scholars

    print(f"Scholars to process: {len(todo)}/{len(scholars)}")

    if args.limit:
        todo = todo[: args.limit]
        print(f"  Limited to {args.limit}")

    success, failed, skipped = 0, 0, 0
    for i, scholar in enumerate(todo):
        name = scholar["scholar_name"]
        sid = scholar["scholar_id"]
        inst = scholar["scholar_institution"]
        filename = pic_filename(name, sid)
        output_path = PICS_DIR / filename

        print(f"[{i + 1}/{len(todo)}] {name}")

        if args.dry_run:
            print(f'  Would search: "{name} {inst} neuroscience researcher headshot"')
            continue

        try:
            urls = search_face_images(name, inst, api_key)
        except requests.RequestException as e:
            print(f"  Search error: {e}")
            failed += 1
            continue

        if not urls:
            print("  No images found")
            skipped += 1
            continue

        downloaded = False
        for url in urls:
            try:
                download_and_save(url, output_path)
                conn = get_connection()
                init_db(conn)
                ensure_scholar(conn, sid, name, inst)
                upsert_profile_pic(conn, sid, filename)
                conn.close()
                print(f"  Saved {filename}")
                success += 1
                downloaded = True
                break
            except Exception as e:
                print(f"  Failed: {e}")

        if not downloaded:
            print("  All URLs failed")
            failed += 1

        time.sleep(0.3)

    print(f"\nDone: {success} saved, {skipped} no results, {failed} errors")


if __name__ == "__main__":
    main()
