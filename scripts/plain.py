#!/usr/bin/env python3
"""Rows for the *plain* adapter (next-training-scope.md, Plug-in 2): ordinary student sentences, typing slips and all, read as story.
Source: PERSUADE 2.0 (Crossley and others, 2024, CC BY-NC-SA 4.0), its training split only; its test split is the test.
The rule for rows (mine until he changes it): every sentence of five words or more, from essays of any score, is story (2), except
sentences that quote (mostly the prompt's sources), sentences carrying the corpus's anonymising tags (Generic_Name and the like) and
sentences with a simile's shape (the few analogies stay out rather than be taught as story). Each story sentence of the twin share
has an unwanted twin (0): the same words shuffled, case and slips as written (lesson 13z62). Essays, not sentences, are split into
train, tune and held, so no essay feeds two parts. i7's own rows are mixed in, marked "source": "i7", so the adapter keeps what the
base knows. The test: 3,000 sentences of the test split by the same rule, and their shuffled twins (tests/persuade-test.jsonl).
usage: python plain.py <folder holding persuade_corpus_2.0_train.csv and persuade_corpus_2.0_test.csv>   (writes data-ad-plain/)
"""
import collections, csv, glob, json, os, random, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY, TWINS, REPLAY = (6000, 750, 750), (3000, 375, 375), (10000, 1250, 1250)
SIM = re.compile(r"\b(?:(?<!would )(?<!feel )(?<!looks )(?<!look )(?<!seem )(?<!sounds )like an? |as if |as though |is like |are like |just like |similar to a )", re.I)
TAG = re.compile(r"\b[A-Za-z]+_[A-Za-z_]+\b|\b[A-Z]{2,}_?NAME\b")
csv.field_size_limit(10**9)


def sentences(text):
    return [s.strip() for s in re.split(r"\n+|(?<=[.!?])\s+", text) if len(s.split()) >= 5 and not SIM.search(s) and not TAG.search(s) and not re.search(r"[\"“”]", s)]


def essays(path):
    out = {}
    for row in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
        out.setdefault(row["essay_id"], row["full_text"])
    return list(out.values())


def twin(s, rng):
    w = s.split()
    for _ in range(20):
        rng.shuffle(w)
        if " ".join(w) != s:
            return " ".join(w)


def main(src):
    rng = random.Random(71)
    tests = {json.loads(l)["text"] for f in glob.glob(os.path.join(HERE, "tests/**/*.jsonl"), recursive=True) for l in open(f) if l.strip()}
    es = essays(os.path.join(src, "persuade_corpus_2.0_train.csv"))
    rng.shuffle(es)
    cut = [0, int(len(es) * 0.8), int(len(es) * 0.9), len(es)]
    os.makedirs(os.path.join(HERE, "data-ad-plain"), exist_ok=True)
    for k, part in enumerate(("train", "tune", "held")):
        pool = list(dict.fromkeys(s for e in es[cut[k]:cut[k + 1]] for s in sentences(e) if s not in tests))
        story = rng.sample(pool, STORY[k])
        rows = [{"label": 2, "kind": "persuade", "source": "persuade-2.0", "text": s} for s in story]
        rows += [{"label": 0, "kind": "persuade-shuffled", "source": "persuade-2.0", "text": t} for t in (twin(s, rng) for s in story[:TWINS[k]]) if t]
        # no swapped-word twins from 1 November 2026 (his rules sheet, grounding/rules-keys.txt, rule 2: a swapped sentence is unwanted only if it is
        # meaningless, which takes a reader); the rows built with them before that stand
        i7 = [json.loads(l) for l in open(os.path.join(HERE, f"data-{os.environ.get('ARM', 'i7')}/{part}.jsonl"))]
        rows += [{**x, "source": "base"} for x in rng.sample(i7, REPLAY[k])]
        rng.shuffle(rows)
        with open(os.path.join(HERE, f"data-ad-plain/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        kinds = collections.Counter("base" if r["source"] == "base" else r["kind"] for r in rows)
        print(f"data-ad-plain/{part}.jsonl: {len(rows)} rows from {cut[k + 1] - cut[k]} essays ({len(pool)} sentences by the rule)", kinds)
    if os.path.exists(os.path.join(HERE, "tests/persuade-test.jsonl")):   # a test stands once drawn, so every model meets the same one
        return
    test = list(dict.fromkeys(s for e in essays(os.path.join(src, "persuade_corpus_2.0_test.csv")) for s in sentences(e)))
    pairs = [(s, t) for s, t in ((s, twin(s, rng)) for s in rng.sample(test, 3000)) if t]   # a sentence no shuffle can change has no twin
    rows = [{"label": 2, "kind": "persuade", "text": s} for s, _ in pairs] + [{"label": 0, "kind": "persuade-shuffled", "text": t} for _, t in pairs]
    with open(os.path.join(HERE, "tests/persuade-test.jsonl"), "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    print(f"tests/persuade-test.jsonl: {len(rows)} rows, from {len(test)} test-split sentences by the rule")


if __name__ == "__main__":
    main(sys.argv[1])
