"""Record the cleaned chapter boundaries and source provenance."""
import hashlib
import json
from datetime import date
from pathlib import Path

from src.ingestion import load_chapters


starter = Path(__file__).resolve().parents[1]
repo = starter.parent
raw = starter / "data" / "pride_and_prejudice_raw.txt"
source_url = "https://www.gutenberg.org/ebooks/1342"
pages = load_chapters(starter / "data" / "chapters", "pride_and_prejudice", source_url)
manifest = {
    "source_id": "pride_and_prejudice",
    "title": "Pride and Prejudice",
    "author": "Jane Austen",
    "source_path_or_url": source_url,
    "local_raw_path": "starter/data/pride_and_prejudice_raw.txt",
    "license_or_permission": "Project Gutenberg lists the text as public domain in the USA; verify local rights and Project Gutenberg terms before redistributing.",
    "accessed_at": date.today().isoformat(),
    "snapshot": "Project Gutenberg eBook #1342; raw file states updated September 1, 2026",
    "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
    "count_rule": "One source chapter with at least 1500 characters after Unicode and whitespace normalization; front matter, illustrations, printer note, and license excluded.",
    "pages": [{"page_id": f"chapter_{page.page:02d}", "page": page.page,
               "normalized_characters": len(page.text)} for page in pages],
}
destination = repo / "data" / "manifest.json"
destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {destination}: {len(pages)} eligible chapters")
