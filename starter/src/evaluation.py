"""Exact gold evidence checks; manual labels remain separate."""
import re
from typing import Any


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    evidence = re.sub(r"\s+", " ", question["evidence_quote"]).strip()
    for hit in hits:
        hit["gold_evidence_hit"] = (
            hit["document_id"] == question["gold_source_id"]
            and hit["page"] == int(question["gold_page"].split("_")[1])
            and evidence in re.sub(r"\s+", " ", hit["text"])
        )
    return {"question": question, "hits": hits,
            "hit1": bool(hits and hits[0]["gold_evidence_hit"]),
            "hit3": any(hit["gold_evidence_hit"] for hit in hits[:3])}


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(traces)
    return {"questions": total, "hit1": sum(trace["hit1"] for trace in traces),
            "evidence_hit3": sum(trace["hit3"] for trace in traces)}
