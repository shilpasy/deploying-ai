#!/usr/bin/env python3
from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


RAW_DIR = Path("05_src/assignment_chat/data/raw")
INDEX_HTML_PATH = RAW_DIR / "podscripts_goodinside_index.html"
OUT_DIR = RAW_DIR / "podscripts_episodes"

BASE_URL = "https://podscripts.co"


def sanitize_filename(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-]+", "", s)
    return s[:140] if len(s) > 140 else s


def extract_episode_urls(index_html: str) -> list[str]:
    """
    Extract episode links from podscripts index HTML.

    Typical episode URLs look like:
    /podcasts/good-inside-with-dr-becky/<episode-slug>/
    """
    hrefs = re.findall(r'href="([^"]+)"', index_html)
    urls: list[str] = []
    for h in hrefs:
        # Make absolute
        u = urljoin(BASE_URL, h)

        p = urlparse(u)
        if p.netloc != "podscripts.co":
            continue

        # Keep episode pages under the Good Inside podcast path
        # Avoid the index page itself.
        if p.path.startswith("/podcasts/good-inside-with-dr-becky/") and p.path != "/podcasts/good-inside-with-dr-becky/":
            # Normalize to no query/fragment
            clean = f"{p.scheme}://{p.netloc}{p.path}"
            urls.append(clean.rstrip("/") + "/")

    # De-dupe while preserving order
    seen = set()
    uniq = []
    for u in urls:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def download_html(url: str, out_path: Path, timeout: int = 30) -> None:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (edu project)"})
    r.raise_for_status()
    out_path.write_text(r.text, encoding="utf-8")


def main(limit: int = 0, sleep_s: float = 0.4) -> None:
    if not INDEX_HTML_PATH.exists():
        raise FileNotFoundError(f"Missing index HTML: {INDEX_HTML_PATH}. Run download_sources.py first.")

    index_html = INDEX_HTML_PATH.read_text(encoding="utf-8", errors="ignore")
    episode_urls = extract_episode_urls(index_html)

    if not episode_urls:
        print("No episode URLs found. The site HTML may have changed.")
        return

    if limit and limit > 0:
        episode_urls = episode_urls[:limit]

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(episode_urls)} episode pages to download.")
    for i, url in enumerate(episode_urls, start=1):
        slug = urlparse(url).path.rstrip("/").split("/")[-1]
        fname = sanitize_filename(slug) or f"episode_{i:04d}"
        out_path = OUT_DIR / f"{fname}.html"

        if out_path.exists():
            print(f"[{i}/{len(episode_urls)}] exists: {out_path.name}")
            continue

        print(f"[{i}/{len(episode_urls)}] downloading: {url}")
        try:
            download_html(url, out_path)
        except Exception as e:
            print(f"  !! failed: {e}")
            continue

        time.sleep(sleep_s)

    print(f"\nDone. Files saved under: {OUT_DIR}")


if __name__ == "__main__":
    import sys
    # usage:
    #   python download_podscripts_episodes.py           (downloads all)
    #   python download_podscripts_episodes.py 20        (downloads first 20)
    limit = 0
    if len(sys.argv) >= 2:
        limit = int(sys.argv[1])
    main(limit=limit)
