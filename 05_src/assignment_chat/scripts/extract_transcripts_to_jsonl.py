#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT_05_SRC = Path(__file__).resolve().parents[2]
EP_DIR = ROOT_05_SRC / "assignment_chat" / "data" / "raw" / "podscripts_episodes"
OUT_JSONL = ROOT_05_SRC / "assignment_chat" / "data" / "derived" / "parenting_corpus.jsonl"

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t:
                self._chunks.append(t)

    def text(self) -> str:
        raw = " ".join(self._chunks)
        raw = re.sub(r"\s+", " ", raw).strip()
        return raw

def extract_title(html: str, fallback: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return fallback
    title = re.sub(r"\s+", " ", m.group(1)).strip()
    return title or fallback

def main():
    if not EP_DIR.exists():
        raise FileNotFoundError(f"Missing {EP_DIR} (you already have it—double-check path)")

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(EP_DIR.glob("*.html"))
    print(f"Found {len(files)} transcript HTML files")

    rows = []
    for fp in files:
        html = fp.read_text(encoding="utf-8", errors="ignore")
        title = extract_title(html, fp.stem)

        parser = TextExtractor()
        parser.feed(html)
        text = parser.text()

        # Basic cleanup: remove nav-ish boilerplate if it appears
        # (keep it light; we’ll rely on chunking + retrieval)
        if len(text) < 500:
            continue

        rows.append({
            "source": "transcript",
            "title": title,
            "section": fp.stem,
            "text": text
        })

    print(f"Prepared {len(rows)} transcript records")

    with OUT_JSONL.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Appended to: {OUT_JSONL}")

if __name__ == "__main__":
    main()