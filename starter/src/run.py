"""Ingest one corpus, compare A/B/C, and save reproducible retrieval traces."""
import json
import os
import time
from importlib.metadata import version
from pathlib import Path

from dotenv import load_dotenv

from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, summarize
from .ingestion import load_chapters
from .store import PgVectorStore


def main() -> None:
    starter = Path(__file__).resolve().parents[1]
    repo = starter.parent
    load_dotenv(starter / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("Set DATABASE_URL in starter/.env")
    model_name = os.getenv("EMBEDDING_MODEL") or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    source = "https://www.gutenberg.org/ebooks/1342"
    pages = load_chapters(starter / "data" / "chapters", "pride_and_prejudice", source)
    questions = [json.loads(line) for line in (repo / "benchmark" / "questions.jsonl")
                 .read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(questions) < 20:
        raise ValueError("Benchmark needs at least 20 questions")

    fixed = [chunk for page in pages for chunk in fixed_size(page, 800, 80)]
    paragraphs = [chunk for page in pages for chunk in by_paragraph(page, 800)]
    chunks = {"A": fixed, "B": paragraphs, "C": paragraphs}
    embedder = MyEmbedder(model_name)
    store = PgVectorStore(database_url, embedder.dimensions)
    store.create_schema()
    results = repo / "results"
    results.mkdir(exist_ok=True)
    ingest = {}
    paragraph_vectors = None
    for strategy, data in chunks.items():
        start = time.perf_counter()
        vectors = paragraph_vectors if strategy == "C" else embedder.embed_documents([c.text for c in data])
        if strategy == "B":
            paragraph_vectors = vectors
        store.upsert(strategy, data, vectors)
        ingest[strategy] = {"chunks": len(data), "characters": sum(len(c.text) for c in data),
                            "seconds": round(time.perf_counter() - start, 3),
                            "vectors_reused_from": "B" if strategy == "C" else None}

    traces = []
    summary = {}
    for split in ("dev", "test"):
        split_questions = [q for q in questions if q["split"] == split]
        query_vectors = {q["id"]: embedder.embed_query(q["question"]) for q in split_questions}
        for strategy in chunks:
            group = []
            for question in split_questions:
                filters = question.get("filter") if strategy == "C" else None
                hits = store.search(strategy, query_vectors[question["id"]], 3, filters)
                trace = evaluate_query(question, hits)
                trace["strategy"] = strategy
                group.append(trace)
                traces.append(trace)
            summary[f"{strategy}_{split}"] = summarize(group)
        if split == "dev":
            # Selection rule is fixed before viewing the test split.
            selected = max(chunks, key=lambda s: (summary[f"{s}_dev"]["evidence_hit3"],
                                                   summary[f"{s}_dev"]["hit1"],
                                                   -ingest[s]["chunks"]))

    (results / "traces.jsonl").write_text(
        "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in traces), encoding="utf-8")
    report = {"model": model_name, "dimensions": embedder.dimensions,
              "sentence_transformers_version": version("sentence-transformers"),
              "psycopg_version": version("psycopg"), "store": "PostgreSQL + pgvector",
              "metric": "exact cosine", "cost_usd": 0,
              "selection_rule": "Highest dev Evidence Hit@3, then dev Hit@1, then fewer chunks",
              "selected_on_dev": selected, "ingest": ingest, "retrieval": summary}
    (results / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")
    print(json.dumps({"selected_on_dev": selected, "retrieval": summary}, indent=2))


if __name__ == "__main__":
    main()
