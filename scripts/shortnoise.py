#!/usr/bin/env python3
"""Arm I7 (31 Oct 2026, 01:50). His word: "Another round - figure it out". Arm I6 met the rule except the held-out sets (−15 rows
each), nearly all swapped-word nonsense read as story. The lines it lost are short: 12.6 words on average against 17.7 for those it
still reads right, 57% of them twelve words or fewer against 25%, and more of them typed in lower case (43% against 32%). Arms I4 to
I6 added short and casually typed story (short story, fragments, chatty lines, testers' sentences) but no short, casual swapped-word
nonsense, and the story share of the rows rose from 23% to 27%. So arm I7 is arm I6's rows plus the missing twin:
  short swapped   0  i3's swapped-word rows cut at a word boundary to 8 to 14 words, half typed in lower case without a stop
  short shuffled  0  i3's shuffled-word rows cut the same way
No row is a sentence of any test set.
usage: python shortnoise.py   (reads data-i6/, writes data-i7/)
"""
import glob, json, os, random

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PER = {"short-swapped": (4000, 500, 500), "short-shuffled": (2000, 250, 250)}


def cut(s, rng):
    w = s.rstrip(".!?").split()
    if len(w) < 9: return None
    t = " ".join(w[:rng.randint(8, min(14, len(w) - 1))])
    return t.lower() if rng.random() < 0.5 else t[:1].upper() + t[1:] + "."


def main():
    tests = {json.loads(l)["text"] for f in glob.glob(os.path.join(HERE, "tests/**/*.jsonl"), recursive=True) for l in open(f) if l.strip()}
    rng = random.Random(67)
    os.makedirs(os.path.join(HERE, "data-i7"), exist_ok=True)
    for k, part in enumerate(("train", "tune", "held")):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-i6/{part}.jsonl"))]
        made = {r["text"] for r in rows} | tests
        pools = {"short-swapped": [r["text"] for r in rows if r["kind"] == "swapped"], "short-shuffled": [r["text"] for r in rows if r["kind"] == "noise" and len(r["text"].split()) >= 9]}
        added = []
        for kind, pool in pools.items():
            got, tries = 0, 0
            while got < PER[kind][k] and tries < 200000:
                tries += 1; t = cut(rng.choice(pool), rng)
                if t and t not in made:
                    made.add(t); got += 1; added.append({"label": 0, "kind": kind, "source": "shortnoise.py", "text": t})
        out = rows + added
        rng.shuffle(out)
        with open(os.path.join(HERE, f"data-i7/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in out)
        print(f"data-i7/{part}.jsonl: {len(out)} rows; added", {kd: sum(r["kind"] == kd for r in added) for kd in PER})


if __name__ == "__main__":
    main()
