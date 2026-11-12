"""Audit prepared splits without sending data to an external service."""
import argparse
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from backend.rag.prompts import messages
from local_finetuning.prepare_data import QUOTAS


def audit(root, previous=None):
    manifest = json.loads((root / 'manifest.json').read_text())
    assert manifest['counts'] == QUOTAS
    splits = {}
    for split in ('train', 'valid', 'test'):
        rows = [json.loads(line) for line in (root / f'{split}.records.jsonl').read_text().splitlines()]
        splits[split] = rows
        assert len({r['id'] for r in rows}) == len(rows)
        assert dict(Counter(r['category'] for r in rows)) == manifest['counts'][split]
        assert all(0 < r['tokens'] <= manifest['max_tokens'] for r in rows)
        assert not ({r['id'] for r in rows} & set(manifest.get('review_exclusions', {})))
        assert sum(r['tokens'] for r in rows) == manifest['tokens'][split]
    for a, b in itertools.combinations(splits, 2):
        for field in ('id', 'group', 'context_hash'):
            assert not ({r[field] for r in splits[a]} & {r[field] for r in splits[b]}), (a, b, field)
    for name, expected in manifest['sha256'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected
    for split in ('train', 'valid'):
        training = [json.loads(line) for line in (root / f'{split}.jsonl').read_text().splitlines()]
        assert len(training) == len(splits[split])
        for conversation, record in zip(training, splits[split]):
            assert [m['weight'] for m in conversation['messages']] == [0, 0, 1]
            expected = [dict(m, weight=0) for m in messages(record['question'], record['chunks'])]
            expected.append({'role': 'assistant', 'content': record['answers'][0], 'weight': 1})
            assert conversation['messages'] == expected
    assert not (root / 'test.jsonl').exists()
    report = {'status': 'passed', 'counts': {s: len(r) for s, r in splits.items()},
              'token_ranges': {s: [min(r['tokens'] for r in rows), max(r['tokens'] for r in rows)] for s, rows in splits.items()},
              'checks': ['category quotas', 'token limits and totals', 'disjoint IDs, groups and contexts', 'file hashes', 'assistant-only weights and targets', 'no upload-format test file']}
    if previous:
        for name in ('valid.jsonl', 'valid.records.jsonl', 'test.records.jsonl'):
            assert (root / name).read_bytes() == (previous / name).read_bytes(), name
        report['frozen_validation_and_test'] = 'unchanged'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--previous", type=Path, help="Original dataset directory; validation and test must be unchanged")
    args = parser.parse_args()
    report = audit(args.input, args.previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
