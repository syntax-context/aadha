#!/usr/bin/env python3
"""The marks re-keyed on his words of 30 October 2026: "abstract poetic nonsense is condered undesirable kind of noise. the 15 is the
desirable noise. undesirable noise can be upto 2% only", after "more than the normal amount of abstraction, layered meaning, analogy
etc are considered noise but are the desirable kind of noise" and "so e e cummings kind of is considered the desirable kind of noise".
  2 story: plain writing and the everyday idiom.
  1 desirable noise: more than the everyday amount of abstraction, layered meaning or analogy, and grammar bent on purpose.
  0 undesirable noise: gibberish (shuffled words, word piles, random letters), and nonsense without meaning: abstract poetic
    nonsense, swapped-word nonsense, invented words.
Arm I is arm H's rows with these marks. The hand sets and both fixed held-out sets are re-keyed into tests/rekeyed/; the originals
stay as they were, as the record of the earlier keys.
Arm I was trained on the marks as they stood at 13:05, bent grammar as desirable noise; arm I2 (widen.py) drops those rows.
usage: python rekey.py [--tests]   (--tests re-keys only the hand sets and the held-out sets, leaving data-i/ as arm I was trained on it)
"""
import json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNDESIRABLE = {"noise", "swapped", "invented", "poetic", "poetic-broad", "nonsense"}
DESIRABLE_TEXT = {"for days the sky held its breath over the city", "my street smelled of wet earth and relief"}


def mark(r):
    kind, label = r.get("kind", ""), r["label"]
    if kind == "test-text":   # arm G's copies of the test texts: their noise lines are poetic nonsense, two lines are layered meaning
        if r["text"].rstrip(".").lower() in DESIRABLE_TEXT: return 1
        return 0 if label == 1 else label
    if kind == "bent": return None   # grammar bent on purpose (hand-v10): left out of the measure with the cummings thread, 30 Oct, 14:25
    if kind in ("layered", "claim", "casual-layered", "wry"): return 1   # claim: hand-v13; casual-layered and wry: hand-v14
    if kind in UNDESIRABLE or label == 0: return 0
    if label == 1: return 0   # any other kind once keyed grammar without sense: meaning gone, so undesirable
    return 2


def rewrite(src, dst):
    rows = [json.loads(l) for l in open(os.path.join(HERE, src))]
    for r in rows: r["label"] = mark(r)
    rows = [r for r in rows if r["label"] is not None]
    os.makedirs(os.path.dirname(os.path.join(HERE, dst)), exist_ok=True)
    with open(os.path.join(HERE, dst), "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    return {k: sum(r["label"] == k for r in rows) for k in (0, 1, 2)}


if __name__ == "__main__":
    for part in ("train", "tune", "held") if "--tests" not in sys.argv else ():
        print(f"data-i/{part}.jsonl", rewrite(f"data-h/{part}.jsonl", f"data-i/{part}.jsonl"))
    for src in ["data-b/held.jsonl", "data-c/held.jsonl"] + [f"tests/hand-v{n}.jsonl" for n in [*range(1, 11), 12, 13, 14]]:
        dst = "tests/rekeyed/" + (os.path.basename(src) if src.startswith("tests") else src.replace("data-", "held-").replace("/held", ""))
        print(dst, rewrite(src, dst))
