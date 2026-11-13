"""Check scoring edge cases and consistency of the submitted results."""
import json
import unittest
from pathlib import Path

from src.evaluation import evaluate_query, summarize


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.question = {
            "gold_source_id": "book", "gold_page": "chapter_02",
            "evidence_quote": "complete evidence here",
        }

    def hit(self, source="book", page=2, text="complete evidence here"):
        return {"document_id": source, "page": page, "text": text}

    def test_hit_at_one_and_three_require_complete_evidence_and_provenance(self):
        trace = evaluate_query(self.question, [
            self.hit(text="complete evidence"),
            self.hit(source="other"),
            self.hit(text="complete\n evidence here"),
        ])
        self.assertFalse(trace["hit1"])
        self.assertTrue(trace["hit3"])
        self.assertEqual([False, False, True], [h["gold_evidence_hit"] for h in trace["hits"]])

        wrong_page = evaluate_query(self.question, [self.hit(page=3)])
        self.assertFalse(wrong_page["hit3"])
        self.assertEqual({"questions": 2, "hit1": 0, "evidence_hit3": 1},
                         summarize([trace, wrong_page]))

    def test_submitted_summary_matches_all_top_three_traces(self):
        repo = Path(__file__).resolve().parents[2]
        summary = json.loads((repo / "results" / "summary.json").read_text(encoding="utf-8"))
        traces = [json.loads(line) for line in (repo / "results" / "traces.jsonl")
                  .read_text(encoding="utf-8").splitlines()]
        self.assertEqual(60, len(traces))
        self.assertTrue(all(len(trace["hits"]) == 3 for trace in traces))
        for strategy in ("A", "B", "C"):
            for split, count in (("dev", 15), ("test", 5)):
                group = [trace for trace in traces if trace["strategy"] == strategy
                         and trace["question"]["split"] == split]
                self.assertEqual(count, len(group))
                self.assertEqual(summary["retrieval"][f"{strategy}_{split}"], summarize(group))


if __name__ == "__main__":
    unittest.main()
