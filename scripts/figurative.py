#!/usr/bin/env python3
"""Rows for the *figurative* adapter (31 October 2026, his words: "adapter for ... analogies/metaphors/idioms"): fresh metaphors and
similes read as the good noise, stock idioms read as common coin, the fourth mark (soup i8 onward). Sources, licences read at source
on 31 October (by the rule: the licence must allow derived work; none at source counts as excluded):
  Fig-QA (Liu and others, 2022, MIT): metaphors and similes written by people, each with what it means said plainly. The metaphor is
    the good noise (1); its meaning, a real plain twin in the same subject, is story (2). Split by question, so a pair stays together.
    From 1 November 2026 a Fig-QA sentence is a row only once he has read and keyed it (his rules sheet, grounding/rules-keys.txt,
    rule 6: "not necessarily. all 1 entries have to be read"); his key, in grounding/keys.jsonl, is its label.
  ID10M (Tedeschi and others, 2022, CC BY-NC-SA 4.0), English, read from data-id10m/ (literal.py): a sentence holding a tagged idiom is
    common coin (3), and its literal twin, the same sentence with the idiom said plainly, is story (2) (rules 7 and 8, his yes). On i8
    the idiom rows stood without literal twins, and the adapter read 952 of 3,000 PERSUADE story lines as common coin (lesson 13z66).
Each kind has shuffled twins in its own form (0, rule 1, his yes; lesson 13z62). No swapped-word twins from 1 November (rule 2: unwanted
only if meaningless, which takes a reader); the rows built with them before that stand. The base's own rows (data-$ARM/) are mixed in
("source": "base").
usage: ARM=i9 python figurative.py <sources folder holding figqa/>   (writes data-ad-figurative/)
"""
import collections, csv, glob, json, os, random, sys
from keys import keyed, read1

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLAY = (10000, 1250, 1250)
KEYS, READ = keyed(), read1()


def figqa(src):
    """{question: [(metaphor, its meaning)]}"""
    out = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(src, "figqa/train_l.csv"), encoding="utf-8")):
        out[r["qid"]].append((r["startphrase"].strip(), r["ending1" if r["labels"] == "0" else "ending2"].strip()))
    return out


def shuffled(s, rng):
    w = s.split()
    rng.shuffle(w)
    return " ".join(w)


def main(src):
    rng = random.Random(79)
    tests = {json.loads(l)["text"] for f in glob.glob(os.path.join(HERE, "tests/**/*.jsonl"), recursive=True) for l in open(f) if l.strip()}
    q = figqa(src)
    qids = sorted(q); rng.shuffle(qids)
    cut = [0, int(len(qids) * 0.8), int(len(qids) * 0.9), len(qids)]
    os.makedirs(os.path.join(HERE, "data-ad-figurative"), exist_ok=True)
    for k, part in enumerate(("train", "tune", "held")):
        pairs = [p for i in qids[cut[k]:cut[k + 1]] for p in q[i]]
        # a metaphor is a row once read: his key, or Claude Code's reading of every good-noise row (rule 6, then his word of 1 November:
        # "you (claude code) read everything 1 including what stands"); the plain meanings beside them only once he has keyed them
        good = [m for m in dict.fromkeys(m for m, _ in pairs) if m not in tests and (m in KEYS or READ.get(m))]
        plain = [m for m in dict.fromkeys(e for _, e in pairs) if m not in tests and m in KEYS]
        idi = [r for r in map(json.loads, open(os.path.join(HERE, f"data-id10m/{part}.jsonl"))) if r["text"] not in tests]
        it = [r["text"] for r in idi]
        rows = [{"label": KEYS.get(s, 1), "kind": "figqa-metaphor", "source": "fig-qa", "text": s} for s in good]
        rows += [{"label": KEYS[s], "kind": "figqa-meaning", "source": "fig-qa", "text": s} for s in plain]
        rows += [{"label": 3, "kind": "id10m-idiom", "source": "id10m", "text": s} for s in it]
        rows += [{"label": 2, "kind": "id10m-literal", "source": "id10m", "text": r["literal"]} for r in idi if r["literal"]]
        rows += [{"label": 0, "kind": "shuffled-metaphor", "source": "fig-qa", "text": shuffled(s, rng)} for s in good[:len(good) // 3]]
        rows += [{"label": 0, "kind": "shuffled-idiom", "source": "id10m", "text": shuffled(s, rng)} for s in it[:len(it) // 3]]
        base = [json.loads(l) for l in open(os.path.join(HERE, f"data-{os.environ.get('ARM', 'i7')}/{part}.jsonl"))]
        rows += [{**x, "source": "base"} for x in rng.sample(base, REPLAY[k])]
        rng.shuffle(rows)
        with open(os.path.join(HERE, f"data-ad-figurative/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        print(f"data-ad-figurative/{part}.jsonl: {len(rows)} rows", collections.Counter("base" if r["source"] == "base" else r["kind"] for r in rows))


if __name__ == "__main__":
    main(sys.argv[1])
