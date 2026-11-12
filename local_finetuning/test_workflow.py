import unittest

from local_finetuning.prepare_data import digest, normalize, partition, select
from local_finetuning.prompts import ABSTENTION, messages


class DatasetTests(unittest.TestCase):
    def test_null_or_invalid_neural_fields_are_rejected(self):
        for field in ("context", "question", "answer"):
            for value in (None, 123, "   "):
                with self.subTest(field=field, value=value):
                    row = {"context": "A is here", "question": "Who?", "answer": "A"}
                    row[field] = value
                    self.assertIsNone(normalize("neural", row, 0))

    def test_squad_missing_evidence_uses_abstention(self):
        row = normalize("squad", {"title": "Page", "question": "Who?", "context": "Nothing here.",
                                  "answers": {"text": []}}, 1)
        self.assertEqual(row["answers"], [ABSTENTION])
        self.assertFalse(row["answerable"])

    def test_squad_article_group_spans_paragraphs(self):
        rows = [normalize("squad", {"title": "Page", "question": "Who?", "context": text,
                                   "answers": {"text": ["A"]}}, i)
                for i, text in enumerate(["A is here", "A is there"])]
        self.assertEqual(rows[0]["group"], rows[1]["group"])

    def test_selection_is_deterministic_and_disjoint(self):
        rows = [{"id": str(i), "group": f"article{i}", "category": "neural",
                 "context_hash": digest(f"text{i}"), "question": "Who?"} for i in range(500)]
        quotas = {split: {"neural": 5} for split in ("train", "valid", "test")}
        selected = select(rows + rows, quotas)
        self.assertEqual(selected, select(rows + rows, quotas))
        self.assertEqual(len({r["id"] for rs in selected.values() for r in rs}), 15)
        for split, records in selected.items():
            self.assertTrue(all(partition(r["group"]) == split for r in records))

    def test_cross_source_duplicate_context_cannot_leak(self):
        groups = {split: next(f"group{i}" for i in range(1000) if partition(f"group{i}") == split)
                  for split in ("train", "valid", "test")}
        rows = [{"group": group, "category": "neural", "context_hash": "same", "question": split}
                for split, group in groups.items()]
        with self.assertRaises(ValueError):
            select(rows, {split: {"neural": 1} for split in groups})

    def test_exclusions_replace_only_the_affected_split(self):
        rows = [{"id": str(i), "group": f"article{i}", "category": "neural",
                 "context_hash": digest(f"text{i}"), "question": "Who?"} for i in range(500)]
        quotas = {split: {"neural": 5} for split in ("train", "valid", "test")}
        before = select(rows, quotas)
        rejected = before["train"][0]["id"]
        after = select(rows, quotas, excluded_ids={rejected})
        self.assertNotIn(rejected, {r["id"] for r in after["train"]})
        self.assertEqual(before["valid"], after["valid"])
        self.assertEqual(before["test"], after["test"])

    def test_insufficient_data_fails_instead_of_silently_shrinking(self):
        with self.assertRaises(ValueError):
            select([])

    def test_prompt_preserves_evidence_and_question(self):
        result = messages("When?", [{"filename": "notes.txt", "text": "On Tuesday."}])
        self.assertIn("From notes.txt:\nOn Tuesday.", result[1]["content"])
        self.assertIn("Question: When?", result[1]["content"])


if __name__ == "__main__":
    unittest.main()
