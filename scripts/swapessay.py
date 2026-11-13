#!/usr/bin/env python3
"""Arm i11 (1 November 2026): soup i10 read 56 unwanted held-b lines as story (i9: 44), mostly swapped-word nonsense, because the essay
rows came in without swapped-word twins (lesson 13z73). His rule 2 (grounding/rules-keys.txt): a swapped sentence is unwanted "only if
it is meaningless". So swapped twins were made of the essay sentences (grounding/swapped-essay.jsonl, twins.py) and read one by one
by Claude Code with Opus for meaninglessness against the About page's definition (grounding/read-0.jsonl, his yes of 15:35 to spend
it); only those read as meaningless enter, as unwanted noise (0). Arm i11 is arm i10's rows plus those, nothing else.
usage: python swapessay.py   (reads data-i10/ and grounding/read-0.jsonl, writes data-i11/)
"""
import collections, json, os, random

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    rng = random.Random(127)
    read = [json.loads(l) for l in open(os.path.join(HERE, "grounding/read-0.jsonl"))]
    os.makedirs(os.path.join(HERE, "data-i11"), exist_ok=True)
    for part in ("train", "tune", "held"):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-i10/{part}.jsonl"))]
        add = [{"label": 0, "kind": "persuade-swapped", "source": "persuade-2.0", "text": r["text"]} for r in read if r["part"] == part and r["meaningless"]]
        rows += add
        rng.shuffle(rows)
        with open(os.path.join(HERE, f"data-i11/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        print(f"data-i11/{part}.jsonl: {len(rows)} rows; by mark", dict(sorted(collections.Counter(r["label"] for r in rows).items())), "; added", len(add))


if __name__ == "__main__":
    main()
