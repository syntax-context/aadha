#!/usr/bin/env python3
"""Arm I5 (30 Oct 2026, 22:20). His word, after i4 failed the rule: "build - fix problems pls". Arm I4 taught that short, broken
and misspelt text is story, and began to read some nonsense as story (swapped-word nonsense on the held-out sets, "under jumped
spoon", a nonsense fragment) and one casual story line as unwanted ("ok so the assignment is due monday right"). Lesson 13z62: a
new story form needs its unwanted twin in the same form. So arm I5 is arm I4's rows plus:
  short gibberish       0  three to five words: a short story sentence shuffled, or words drawn at random from different rows
  nonsense fragments    0  i3's poetic and swapped-word nonsense cut at a comma, or ending in one, as the story fragments are
  casual nonsense       0  i3's swapped-word, shuffled and poetic rows typed casually (lower case, no stop, a trailing comma)
  chatty story          2  plain story typed as people message: lower case, no stop, opening with ok so / so / and then / btw
No row is a sentence of any test set.
usage: python counter.py   (reads data-i4/, writes data-i5/)
"""
import glob, json, os, random

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PER = {"short-gibberish": (3000, 400, 400), "fragment-nonsense": (3000, 400, 400), "casual-nonsense": (4000, 500, 500), "chatty": (2000, 250, 250)}
LEADS = ["ok so ", "so ", "and then ", "btw ", "anyway ", "also "]


def casual(s, rng):
    s = s.lower().rstrip(".!?")
    return s + "," if rng.random() < 0.3 else s


def main():
    tests = {json.loads(l)["text"] for f in glob.glob(os.path.join(HERE, "tests/**/*.jsonl"), recursive=True) for l in open(f) if l.strip()}
    tests |= {t.lower().rstrip(".!?") for t in tests}
    rng = random.Random(61)
    os.makedirs(os.path.join(HERE, "data-i5"), exist_ok=True)
    for k, part in enumerate(("train", "tune", "held")):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-i4/{part}.jsonl"))]
        made = {r["text"] for r in rows} | tests
        short = [r["text"] for r in rows if r["kind"] == "short"]
        words = [w for r in rows if r["kind"] == "meaning" for w in r["text"].lower().rstrip(".!?").split()]
        nonsense = [r["text"] for r in rows if r["kind"] in ("poetic", "poetic-broad", "swapped")]
        noise = [r["text"] for r in rows if r["kind"] in ("swapped", "noise", "poetic")]
        story = [r["text"] for r in rows if r["kind"] == "meaning" and len(r["text"].split()) <= 14]
        added = []
        def fill(kind, label, maker):
            got, tries = 0, 0
            while got < PER[kind][k] and tries < 200000:
                tries += 1; t = maker()
                if t and t not in made:
                    made.add(t); got += 1; added.append({"label": label, "kind": kind, "source": "counter.py", "text": t})
        def gibberish():
            if rng.random() < 0.5 and short:
                w = rng.choice(short).rstrip(".!?").split(); rng.shuffle(w); t = " ".join(w)
            else:
                t = " ".join(rng.sample(words, rng.randint(3, 5)))
            return t.lower() if rng.random() < 0.6 else t[:1].upper() + t[1:] + "."
        fill("short-gibberish", 0, gibberish)
        def fragment():
            s = rng.choice(nonsense); head = s.split(",")[0].rstrip(".!?")
            w = head.split()
            if len(w) > 9: head = " ".join(w[:rng.randint(4, 8)])
            return (head.lower() if rng.random() < 0.4 else head) + ","
        fill("fragment-nonsense", 0, fragment)
        fill("casual-nonsense", 0, lambda: casual(rng.choice(noise), rng))
        fill("chatty", 2, lambda: rng.choice(LEADS) + rng.choice(story).lower().rstrip(".!?"))
        out = rows + added
        rng.shuffle(out)
        with open(os.path.join(HERE, f"data-i5/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in out)
        count = {}
        for r in added: count[r["kind"]] = count.get(r["kind"], 0) + 1
        print(f"data-i5/{part}.jsonl: {len(out)} rows; added {count}")


if __name__ == "__main__":
    main()
