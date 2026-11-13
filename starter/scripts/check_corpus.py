"""Check corpus size, benchmark split, and source-backed gold quotes."""
import json
from pathlib import Path

from src.ingestion import load_chapters


repo = Path(__file__).resolve().parents[2]
pages = load_chapters(repo / "starter" / "data" / "chapters",
                      "pride_and_prejudice", "https://www.gutenberg.org/ebooks/1342")
questions = [json.loads(line) for line in (repo / "benchmark" / "questions.jsonl")
             .read_text(encoding="utf-8").splitlines() if line.strip()]
assert len(pages) >= 30
assert len(questions) >= 20
assert sum(q["split"] == "dev" for q in questions) >= 15
assert sum(q["split"] == "test" for q in questions) >= 5
assert len({q["id"] for q in questions}) == len(questions)
assert sum(bool(q.get("filter")) for q in questions) >= 3
assert any(q["split"] == "test" and q.get("filter") for q in questions)
for question in questions:
    page = int(question["gold_page"].split("_")[1])
    assert question["gold_source_id"] == pages[page - 1].document_id
    assert question["evidence_quote"] in pages[page - 1].text, question["id"]
    if question.get("filter"):
        assert question["filter"] == {"chapter": page}, question["id"]
print(f"Corpus OK: {len(pages)} chapters; benchmark OK: {len(questions)} questions")
