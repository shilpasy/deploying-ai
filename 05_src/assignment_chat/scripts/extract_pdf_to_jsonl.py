#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT_05_SRC = Path(__file__).resolve().parents[2]

PDF_PATH = ROOT_05_SRC / "assignment_chat" / "data" / "raw" / "good-inside_bookey.pdf"
OUT_JSONL = ROOT_05_SRC / "assignment_chat" / "data" / "derived" / "parenting_corpus.jsonl"

def extract_pdf_text() -> list[dict]:
    """
    Extract PDF text with a best-effort approach using libs commonly available in course envs.
    Produces one record per page.
    """
    # Try PyMuPDF first (fitz)
    try:
        import fitz  # type: ignore
        doc = fitz.open(str(PDF_PATH))
        rows = []
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text("text").strip()
            if text:
                rows.append({
                    "source": "pdf",
                    "title": "Good Inside (Bookey summary)",
                    "section": f"page_{i+1}",
                    "text": text
                })
        return rows
    except Exception:
        pass

    # Fall back to pypdf
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(PDF_PATH))
        rows = []
        for i, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if text:
                rows.append({
                    "source": "pdf",
                    "title": "Good Inside (Bookey summary)",
                    "section": f"page_{i+1}",
                    "text": text
                })
        return rows
    except Exception as e:
        raise RuntimeError(
            "Could not extract PDF text. Try installing PyMuPDF or pypdf."
        ) from e

def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"Missing {PDF_PATH}")

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    rows = extract_pdf_text()
    print(f"Extracted {len(rows)} PDF pages with text")

    # Append to existing JSONL (don’t overwrite transcripts we’ll add next)
    with OUT_JSONL.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote to: {OUT_JSONL}")

if __name__ == "__main__":
    main()