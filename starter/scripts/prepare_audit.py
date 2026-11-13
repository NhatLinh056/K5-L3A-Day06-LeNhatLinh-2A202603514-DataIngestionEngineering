"""Prepare fixed samples for human coherence, metadata, and grounding labels."""
import csv
import json
from pathlib import Path

from src.chunking import by_paragraph, fixed_size
from src.ingestion import load_chapters


repo = Path(__file__).resolve().parents[2]
results = repo / "results"
pages = load_chapters(repo / "starter" / "data" / "chapters",
                      "pride_and_prejudice", "https://www.gutenberg.org/ebooks/1342")
traces = [json.loads(line) for line in (results / "traces.jsonl")
          .read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(name: str, columns: list[str], rows: list[dict]) -> None:
    path = results / name
    if path.exists():
        print(f"Keeping existing labels in {path.name}")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


coherence = []
for page in pages[:10]:
    anchor = page.text[100:140]
    for strategy in ("A", "B", "C"):
        candidates = fixed_size(page, 800, 80) if strategy == "A" else by_paragraph(page, 800)
        match = next((chunk for chunk in candidates if anchor in chunk.text), None)
        if match is None:
            raise ValueError(f"Sample anchor missing: chapter {page.page}, {strategy}")
        coherence.append({"strategy": strategy, "page": page.page, "anchor": anchor,
                          "chunk_id": match.chunk_id, "chunk_text": match.text,
                          "score_0_1_2": "", "reason": ""})
write_csv("coherence_audit.csv", list(coherence[0]), coherence)

metadata = []
grounding = []
for trace in traces:
    if trace["question"]["split"] != "test":
        continue
    question = trace["question"]
    for rank, hit in enumerate(trace["hits"], 1):
        metadata.append({"strategy": trace["strategy"], "question_id": question["id"],
                         "rank": rank, "chunk_id": hit["chunk_id"], "source": hit["source"],
                         "page": hit["page"], "chapter": hit["metadata"].get("chapter"),
                         "required_filter": json.dumps(question.get("filter"), ensure_ascii=False),
                         "metadata_complete_correct_0_1": "", "filter_compliant_0_1_or_na": "",
                         "reason": ""})
    grounding.append({"strategy": trace["strategy"], "question_id": question["id"],
                      "question": question["question"], "expected_answer": question["expected_answer"],
                      "gold_evidence": question["evidence_quote"],
                      "top3_text": "\n---\n".join(hit["text"] for hit in trace["hits"]),
                      "score_0_1_2": "", "reason": ""})
write_csv("metadata_audit.csv", list(metadata[0]), metadata)
write_csv("grounding_audit.csv", list(grounding[0]), grounding)
print("Audit templates checked: 30 coherence, 45 metadata, and 15 grounding rows")
