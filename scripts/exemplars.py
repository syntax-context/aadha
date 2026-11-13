#!/usr/bin/env python3
"""Arm G (30 Oct 2026), used only if arm F does not make all eight test pieces dance. His word, quoting the plan: "else: If arm f
doesn't make all eight dance, the next round stops protecting the test texts. Their noise lines are your definition of noise in your
own examples, so they'll go into training directly, and I'll check on a new blind set instead."
The rows of a base arm (the better of E and F), plus every sentence of grounding/test-texts.txt as keyed in tests/hand-v3.jsonl
(26 noise lines as grammar without sense, 39 story lines as meaning), each REPEAT times in the training part only, a third typed as
people type. From here the test texts are training rows, not a test: tests/hand-v7.jsonl, keyed before this arm was built, is the
blind check.
usage: python exemplars.py <base arm>   (writes data-g/)
"""
import importlib.util, json, os, random, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("poetic", os.path.join(HERE, "scripts/poetic.py")); poetic = importlib.util.module_from_spec(spec); spec.loader.exec_module(poetic)
REPEAT = 20


def main(base):
    rng = random.Random(41)
    hand = [json.loads(l) for l in open(os.path.join(HERE, "tests/hand-v3.jsonl"))]
    v7 = {r["text"] for r in map(json.loads, open(os.path.join(HERE, "tests/hand-v7.jsonl")))}
    assert not v7 & {r["text"] for r in hand}, "a blind line is among the test texts"
    os.makedirs(os.path.join(HERE, "data-g"), exist_ok=True)
    for part in ("train", "tune", "held"):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-{base}/{part}.jsonl"))]
        added = [{"label": r["label"], "kind": "test-text", "source": "grounding/test-texts.txt", "text": poetic.typed(r["text"], rng)}
                 for r in hand for _ in range(REPEAT)] if part == "train" else []
        out = rows + added
        rng.shuffle(out)
        with open(os.path.join(HERE, f"data-g/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in out)
        print(f"data-g/{part}.jsonl: {len(rows)} rows of arm {base}, {len(added)} test-text rows added")


if __name__ == "__main__":
    main(sys.argv[1])
