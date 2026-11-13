"""Read the chosen text corpus and keep chapter provenance."""
import re
import unicodedata
from pathlib import Path
from .models import DocumentPage


def load_chapters(directory: Path, document_id: str, source: str) -> list[DocumentPage]:
    paths = sorted(directory.glob("chapter_*.txt"))
    if len(paths) != 61:
        raise ValueError(f"Expected 61 chapters, found {len(paths)}")
    pages = []
    for number, path in enumerate(paths, 1):
        if path.stem != f"chapter_{number:02d}":
            raise ValueError(f"Unexpected chapter file: {path.name}")
        text = normalize_text(path.read_text(encoding="utf-8"))
        if len(text) < 1500:
            raise ValueError(f"Chapter {number} has fewer than 1500 characters")
        pages.append(DocumentPage(document_id, source, number, text, {"chapter": number}))
    return pages


def normalize_text(text: str) -> str:
    """Remove illustration captions and rejoin wrapped lines, preserving paragraphs."""
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n")
    text = text.split("CHISWICK PRESS:", 1)[0]
    while (start := text.find("[Illustration")) != -1:
        depth = 0
        for end in range(start, len(text)):
            if text[end] == "[":
                depth += 1
            elif text[end] == "]":
                depth -= 1
                if depth == 0:
                    text = text[:start] + text[end + 1:]
                    break
        else:
            raise ValueError("Unclosed illustration caption")
    paragraphs = [re.sub(r"\s+", " ", part).strip()
                  for part in re.split(r"\n\s*\n", text)]
    return "\n\n".join(part for part in paragraphs if part)
