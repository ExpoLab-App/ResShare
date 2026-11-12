"""Download public datasets and produce deterministic, document-disjoint JSONL."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

from local_finetuning.prompts import ABSTENTION, PROMPT_VERSION, messages

MODEL = "Qwen/Qwen3.5-9B"
SOURCES = {"neural": "neural-bridge/rag-dataset-12000", "squad": "rajpurkar/squad_v2"}
QUOTAS = {
    "train": {"neural": 3000, "answerable": 1500, "unanswerable": 1500},
    "valid": {"neural": 150, "answerable": 75, "unanswerable": 75},
    "test": {"neural": 25, "answerable": 12, "unanswerable": 13},
}


def digest(value):
    return hashlib.sha256(" ".join(value.split()).encode()).hexdigest()


def partition(group):
    bucket = int(digest(group)[:8], 16) % 100
    return "test" if bucket < 5 else "valid" if bucket < 15 else "train"


def normalize(source, row, index):
    context, question = row.get("context"), row.get("question")
    if not isinstance(context, str) or not isinstance(question, str):
        return None
    context, question = context.strip(), question.strip()
    if not context or not question:
        return None
    if source == "neural":
        if not isinstance(row.get("answer"), str):
            return None
        answers = [row["answer"].strip()]
        category = "neural"
        group = "neural:" + digest(context)
    else:
        answers = [a.strip() for a in row["answers"]["text"] if a.strip()]
        category = "answerable" if answers else "unanswerable"
        # Keep every paragraph/question for a SQuAD article in the same split.
        group = "squad:" + row["title"]
    if category != "unanswerable" and not any(answers):
        return None
    return {
        "id": f"{source}:{row.get('id', index)}", "source": SOURCES[source],
        "group": group, "category": category, "context_hash": digest(context),
        "question": question, "chunks": [{"filename": "document.txt", "text": context}],
        "answers": answers or [ABSTENTION], "answerable": category != "unanswerable",
    }


def select(rows, quotas=QUOTAS, seed=42, excluded_ids=()):
    """Prevent context leakage even if identical text appears in both datasets."""
    rows = list(rows)
    random.Random(seed).shuffle(rows)
    selected = {split: [] for split in quotas}
    counts = {split: Counter() for split in quotas}
    contexts, pairs = {}, set()
    for row in rows:
        if row.get("id") in excluded_ids:
            continue
        split, category = partition(row["group"]), row["category"]
        if counts[split][category] >= quotas[split].get(category, 0):
            continue
        pair = (row["context_hash"], digest(row["question"]))
        if pair in pairs or contexts.get(row["context_hash"], split) != split:
            continue
        selected[split].append(row)
        counts[split][category] += 1
        pairs.add(pair)
        contexts[row["context_hash"]] = split
    for split, targets in quotas.items():
        for category, target in targets.items():
            if counts[split][category] != target:
                raise ValueError(f"Insufficient {split}/{category}: {counts[split][category]} < {target}")
    return selected


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("local_finetuning/data"))
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--exclude-ids", type=Path, help="JSON object mapping rejected IDs to review reasons")
    parser.add_argument("--revisions-from", type=Path, help="Prior manifest whose dataset/model revisions must be reused")
    args = parser.parse_args()
    if args.max_tokens <= 0:
        parser.error("--max-tokens must be positive")
    if args.output.exists():
        parser.error("Output exists; use a new directory to preserve the previous split.")
    from datasets import load_dataset
    from huggingface_hub import HfApi
    from transformers import AutoTokenizer

    api = HfApi()
    previous = json.loads(args.revisions_from.read_text()) if args.revisions_from else None
    exclusions = json.loads(args.exclude_ids.read_text()) if args.exclude_ids else {}
    revision = previous["model_revision"] if previous else api.model_info(MODEL).sha
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=revision)
    rows, revisions, rejected = [], {}, Counter()
    for source, name in SOURCES.items():
        revisions[name] = previous["dataset_revisions"][name] if previous else api.dataset_info(name).sha
        dataset = load_dataset(name, split="train", revision=revisions[name])
        for index, raw in enumerate(dataset):
            row = normalize(source, raw, index)
            if row is None:
                rejected["empty"] += 1
                continue
            conversation = messages(row["question"], row["chunks"]) + [
                {"role": "assistant", "content": row["answers"][0]}
            ]
            length = len(tokenizer.apply_chat_template(
                conversation, tokenize=True, return_dict=False, enable_thinking=False
            ))
            if length > args.max_tokens:
                rejected["overlength"] += 1
                continue  # Never truncate away evidence while retaining the answer.
            row["tokens"] = length
            rows.append(row)
    splits = select(rows, excluded_ids=exclusions)
    args.output.mkdir(parents=True)
    for split, records in splits.items():
        write_jsonl(args.output / f"{split}.records.jsonl", records)
        if split != "test":
            write_jsonl(args.output / f"{split}.jsonl", [
                {"messages": [dict(m, weight=0) for m in messages(r["question"], r["chunks"])] + [
                    {"role": "assistant", "content": r["answers"][0], "weight": 1}
                ]} for r in records
            ])
    manifest = {
        "model": MODEL, "model_revision": revision, "dataset_revisions": revisions,
        "prompt_version": PROMPT_VERSION, "seed": 42, "max_tokens": args.max_tokens,
        "counts": {s: dict(Counter(r["category"] for r in rs)) for s, rs in splits.items()},
        "tokens": {s: sum(r["tokens"] for r in rs) for s, rs in splits.items()},
        "rejected": dict(rejected),
        "review_exclusions": exclusions,
        "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.glob("*.jsonl")},
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
