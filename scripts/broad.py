#!/usr/bin/env python3
"""Arm F (30 Oct 2026, his word "if piece 1 is wrong - fix it. dont give up"): arm E's rows, plus poetic nonsense whose open words
come from the corpus, not from short lists. Soup E still read three lines of the test texts as story at p 0.99 to 1.0, every one
built from words the lists were kept from using, and on hand-v6 (keyed before this arm) its one miss was the same construction as
piece 1's (a sense-noun of a day turning back on itself, ending in a simile), so two things change at once, and the record says so:
 1. breadth: nouns, plural nouns, adjectives and past-tense verbs harvested from arm B's own training sentences (spaCy tags);
 2. a family of shapes for that construction (SHAPES_F), with sense-nouns and a simile verb the hand sets never use.
Every word in the noise lines of hand-v3 to hand-v6 stays out of every pool, and the script refuses to run if one gets in.
usage: python broad.py   (spaCy with en_core_web_sm; reads data-e/ and data-b/train.jsonl, writes data-f/)
"""
import collections, importlib.util, json, os, random, re
import spacy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("poetic", os.path.join(HERE, "scripts/poetic.py")); poetic = importlib.util.module_from_spec(spec); spec.loader.exec_module(poetic)
spec = importlib.util.spec_from_file_location("vegan", poetic.VEGAN); vegan = importlib.util.module_from_spec(spec); spec.loader.exec_module(vegan)

SENSE = "aroma scent brightness loudness heaviness warmth sharpness hue tint glow pitch".split()
SIMILE = "carved built cut sewn".split()
SHAPES_F = [
    "The {sense} of {time} {verb} itself {prep} a {thing} {simile} like a {thing2}.",
    "The {sense} of {gerund} {change} a {adj} {thing}.",
    "A {adj} {shape} {verb} {time} from its own {abstract}.",
    "{Time}'s {abstract} {verb} itself into a {thing} of {things}.",
    "The {sense} of {abstract} {verb_i} {adv} into a {colour} {thing}.",
    "A {thing} {simile} like a {thing2} {verb} the {sense} of {time}.",
]
PER_PART = {"train": 6000, "tune": 750, "held": 750}
# Words that hold a sentence together rather than say what it is about; the hand sets share them with every sentence.
FUNCTION = {"that", "their", "with", "into", "from", "itself", "about", "like", "every", "than", "when", "them", "over", "only", "been", "have",
            "your", "this", "they", "were", "which", "what", "there", "where", "once", "some", "same", "most", "much"}


def excluded():
    """Every word (and its plural) of the hand sets' noise lines, and the words that carry hand-v5's figures of speech."""
    lines = list(poetic.NOISE_LINES)
    for n in (4, 5, 6):
        lines += [r["text"] for r in map(json.loads, open(os.path.join(HERE, f"tests/hand-v{n}.jsonl"))) if r["label"] == 1]
    words = {w.lower() for line in lines for w in re.findall(r"[A-Za-z]+", line) if len(w) > 3} - FUNCTION
    return words | {w + "s" for w in words} | {w[:-1] for w in words if w.endswith("s")} | poetic.V5_FIGURES


def pools(out):
    """Open words by tag from arm B's meaning rows in the training part only, seen at least twice, 4 to 12 letters."""
    nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "parser"])
    texts = [r["text"] for r in map(json.loads, open(os.path.join(HERE, "data-b/train.jsonl"))) if r["label"] == 2]
    count = {t: collections.Counter() for t in ("NN", "NNS", "JJ", "VBD")}
    for doc in nlp.pipe(texts, batch_size=256):
        for tok in doc:
            w = tok.text.lower()
            if tok.tag_ in count and tok.text.isalpha() and tok.text.islower() and 4 <= len(w) <= 12 and w not in out and not vegan.ANIMAL.search(w):
                count[tok.tag_][w] += 1
    return {t: sorted(w for w, n in c.items() if n >= 2) for t, c in count.items()}


def poem(rng, p, closed):
    pick = lambda xs, *not_: rng.choice([x for x in xs if x not in not_])
    a, t = pick(p["NN"]), pick(p["NN"])
    w = {"abstract": a, "abstract2": pick(p["NN"], a), "thing": t, "thing2": pick(p["NN"], t), "things": pick(p["NNS"]), "adj": pick(p["JJ"]),
         "verb": pick(p["VBD"]), "verb_i": pick(p["VBD"]), "sense": pick(SENSE), "simile": pick(SIMILE), **{k: pick(v) for k, v in closed.items()}}
    s = rng.choice(poetic.SHAPES + poetic.SHAPES_D + SHAPES_F)
    s = re.sub(r"\{([A-Z])(\w+)\}", lambda m: w[m.group(1).lower() + m.group(2)].capitalize(), s)
    return re.sub(r"\b([Aa]) (?=[aeiou])", r"\1n ", s.format(**w))


def main():
    out = excluded()
    closed = {"time": poetic.TIME, "colour": poetic.COLOUR, "prep": poetic.PREP, "num": poetic.NUM, **{k: v for k, v in poetic.WIDE.items() if k not in ("abstract", "thing")}}
    closed = {k: [x for x in v if not set(re.findall(r"[a-z]+", x.lower())) & out] for k, v in closed.items()}
    fixed = {w.lower() for s in poetic.SHAPES + poetic.SHAPES_D + SHAPES_F for w in re.findall(r"[A-Za-z]+", re.sub(r"\{\w+\}", "", s))} | set(SENSE + SIMILE)
    fixed = {w for w in fixed if len(w) > 3} - FUNCTION
    assert not fixed & out, f"words of the hand sets' noise lines are in the shapes: {sorted(fixed & out)}"
    p = pools(out)
    print("pools:", {t: len(v) for t, v in p.items()}, "| e.g.", {t: v[::max(1, len(v) // 4)][:4] for t, v in p.items()})
    rng, made = random.Random(37), set()
    os.makedirs(os.path.join(HERE, "data-f"), exist_ok=True)
    for part in ("train", "tune", "held"):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-e/{part}.jsonl"))]
        made |= {r["text"] for r in rows}
        added = []
        while len(added) < PER_PART[part]:
            s = poem(rng, p, closed)
            if s in made or vegan.ANIMAL.search(vegan.ALLOWED.sub("", s)) or set(re.findall(r"[a-z]+", s.lower())) & out:
                continue
            made.add(s)
            added.append({"label": 1, "kind": "poetic-broad", "source": "broad.py", "text": poetic.typed(s, rng)})
        rows += added
        rng.shuffle(rows)
        with open(os.path.join(HERE, f"data-f/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        print(f"data-f/{part}.jsonl: {len(rows) - len(added)} rows of arm e, {len(added)} broad poetic added")


if __name__ == "__main__":
    main()
