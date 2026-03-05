#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import requests

RAW_DIR = Path("05_src/assignment_chat/data/raw")
SOURCES = Path("05_src/assignment_chat/scripts/sources.json")

def download_binary(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=30, headers={"User-Agent": "Mozilla/5.0"}) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)

def download_text(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    out_path.write_text(r.text, encoding="utf-8")

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(SOURCES.read_text(encoding="utf-8"))

    for item in cfg.get("pdfs", []):
        out = RAW_DIR / item["filename"]
        if out.exists():
            print(f"exists: {out}")
        else:
            print(f"downloading pdf: {item['url']} -> {out}")
            download_binary(item["url"], out)

    for item in cfg.get("transcript_pages", []):
        out = RAW_DIR / item["filename"]
        if out.exists():
            print(f"exists: {out}")
        else:
            print(f"downloading html: {item['url']} -> {out}")
            download_text(item["url"], out)

    print("done.")

if __name__ == "__main__":
    main()
