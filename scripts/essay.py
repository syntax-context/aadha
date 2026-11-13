#!/usr/bin/env python3
"""Arm i10 (1 November 2026): the essay register enters the base, under his keys. Soup i9 read about 100 of 3,000 PERSUADE test
sentences as common coin where he keyed story (7 of 130 keyed coin; lesson 13z71): nothing in its rows showed it a school essay.
So arm i10 is arm i9's rows (which stand) with:
  persuade            2   the PERSUADE 2.0 essay sentences plain.py drew for the plain adapter (6,000 / 750 / 750), story by his rule
                          (grounding/rules-keys.txt, rule 3, his yes)
  persuade-shuffled   0   their shuffled twins (rule 1, his yes; lesson 13z62)
and his keys on the essay sentences i9 read as common coin (grounding/essay-train-keys.txt, read into keys.jsonl), which train.py's
row loader applies to these rows as it reads them: where he keyed common coin, the row is common coin. No swapped-word twins (rule 2).
usage: python essay.py   (reads data-i9/ and data-ad-plain/, writes data-i10/)
"""
import collections, json, os, random

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    rng = random.Random(101)
    os.makedirs(os.path.join(HERE, "data-i10"), exist_ok=True)
    for part in ("train", "tune", "held"):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-i9/{part}.jsonl"))]
        essay = [r for r in map(json.loads, open(os.path.join(HERE, f"data-ad-plain/{part}.jsonl"))) if r["kind"] in ("persuade", "persuade-shuffled")]
        rows += essay
        rng.shuffle(rows)
        with open(os.path.join(HERE, f"data-i10/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        print(f"data-i10/{part}.jsonl: {len(rows)} rows; by mark", dict(sorted(collections.Counter(r["label"] for r in rows).items())),
              "; added", collections.Counter(r["kind"] for r in essay))


if __name__ == "__main__":
    main()
