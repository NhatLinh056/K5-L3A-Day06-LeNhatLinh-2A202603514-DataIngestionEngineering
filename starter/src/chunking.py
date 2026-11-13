"""Fixed windows and paragraph-aware chunks for the same source pages."""
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Expected size > overlap >= 0")
    chunks = []
    step = size - overlap
    for index, start in enumerate(range(0, len(page.text), step)):
        content = page.text[start:start + size]
        if not content:
            break
        chunks.append(Chunk(f"{page.document_id}:{page.page}:fixed:{index}",
                            page.document_id, page.source, page.page, content,
                            page.metadata.copy()))
        if start + size >= len(page.text):
            break
    return chunks


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    if max_size <= 0:
        raise ValueError("Expected max_size > 0")
    pieces = []
    for paragraph in page.text.split("\n\n"):
        if len(paragraph) <= max_size:
            pieces.append(paragraph)
        else:
            for start in range(0, len(paragraph), max_size):
                pieces.append(paragraph[start:start + max_size])
    groups = []
    current = ""
    for piece in pieces:
        candidate = f"{current}\n\n{piece}" if current else piece
        if current and len(candidate) > max_size:
            groups.append(current)
            current = piece
        else:
            current = candidate
    if current:
        groups.append(current)
    return [Chunk(f"{page.document_id}:{page.page}:paragraph:{index}",
                  page.document_id, page.source, page.page, content,
                  page.metadata.copy()) for index, content in enumerate(groups)]
