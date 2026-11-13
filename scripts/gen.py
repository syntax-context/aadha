#!/usr/bin/env python3
"""Rows for the sentence reader: each sentence labelled by how it was made, never by a model.
  2 meaning                a real sentence from the open corpus already vetted for rai's base
  1 grammar without sense  the same kind of sentence with its nouns, verbs, adjectives and adverbs swapped for words of the same
                           tag drawn from other sentences, so the grammar stands and the sense goes
  0 noise                  a real sentence's words shuffled, words drawn at random, or random letters
A third of every class is written as people type (lowercase, no closing stop). Sentences are split into train, tune and held
by a hash of the sentence, so no held sentence, or the words it lends, reaches training.
Arm A (--strict, 29 Oct 2026): a swap changes at least three content words and two thirds of them, with words drawn from a
different source than the sentence's, so fewer swapped rows still make sense. Arm B (--strict --invented): as A, and a third of the
grammar-without-sense rows have their content words replaced by invented words that keep the word's ending (-s, -ed, -ing, -ly).
usage: python gen.py <out dir> [--strict] [--invented]   (spaCy with en_core_web_sm; about 7 minutes on the ThinkPad)
"""
import hashlib, importlib.util, json, os, random, re, string, sys
import spacy

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "../../../koher/ARCHIVE-SEPTEMBER-2026/mom-clean-base/data/pretrain")
SOURCES = ["gutenberg", "news", "wikimedia", "pressbooks", "libretexts", "hansard"]
VEGAN = os.path.join(HERE, "../../../koher/tools-dev/koher-engine-core/rai/tests/test_vegan.py")
PER_CLASS = {"train": 12000, "tune": 1500, "held": 1500}
SWAP = {"NOUN", "VERB", "ADJ", "ADV"}

spec = importlib.util.spec_from_file_location("vegan", VEGAN); vegan = importlib.util.module_from_spec(spec); spec.loader.exec_module(vegan)


def clean(s):
    """A sentence a student might write: 6 to 30 words, letters and ordinary punctuation, no animal product."""
    w = s.split()
    return 6 <= len(w) <= 30 and not re.search(r"[^\w\s,.;:'\"!?()-]|\d{3,}|http|www", s) and s[0].isupper() \
        and s[-1] in ".!?" and not vegan.ANIMAL.search(vegan.ALLOWED.sub("", s))


def sentences(nlp, rng):
    """Spans of each source read at random offsets, parsed, and kept where clean."""
    out = []
    for src in SOURCES:
        path = os.path.join(CORPUS, src + ".txt"); size = os.path.getsize(path)
        with open(path, encoding="utf-8", errors="ignore") as f:
            chunks = []
            for _ in range(300):
                f.seek(rng.randrange(size - 20000)); f.readline(); chunks.append(f.read(12000))
        for doc in nlp.pipe(chunks, batch_size=16):
            out += [(src, s) for s in doc.sents if clean(s.text.strip())]
    return out


def split(text):
    h = int(hashlib.sha256(text.encode()).hexdigest(), 16) % 100
    return "held" if h < 8 else "tune" if h < 16 else "train"


def typed(s, rng):
    return s.lower().rstrip(".!?") if rng.random() < 1 / 3 else s


DICT = {w.strip().lower() for w in open("/usr/share/dict/words") if w.strip().isalpha()}
ENDS = {"NNS": "s", "NNPS": "s", "VBD": "ed", "VBN": "ed", "VBG": "ing", "VBZ": "s", "RB": "ly", "JJR": "er", "JJS": "est"}


def invented(tag, rng):
    """A pronounceable word in no dictionary, with the ending its tag asks for."""
    while True:
        w = "".join(rng.choice(["b", "bl", "br", "d", "dr", "f", "fl", "g", "gl", "gr", "k", "m", "n", "p", "pl", "sn", "sk", "st", "t", "tr", "v", "z"])
                    + rng.choice(["a", "e", "i", "o", "u", "oo", "ar", "or", "ee"]) for _ in range(rng.randint(1, 2)))
        w += rng.choice(["", "n", "m", "sh", "nk", "mp", "rl"])
        if w not in DICT:
            return w + ENDS.get(tag, "")


def swapped(sent, pool, rng, strict=False, made_up=False, src=None):
    """Every content word replaced by one with the same fine tag from another sentence (or, made up, by an invented word);
    capitals and spacing kept. Strict: from another source, and at least three changed and two thirds of the content words."""
    out, changed, content = [], 0, sum(t.pos_ in SWAP for t in sent)
    for t in sent:
        by_src = pool.get(t.tag_, {})
        others = [s_ for s_ in by_src if not strict or s_ != src]
        if t.pos_ in SWAP and (others or made_up):
            w = invented(t.tag_, rng) if made_up else rng.choice(by_src[rng.choice(others)])
            if w.lower() != t.text.lower():
                changed += 1
            w = w.capitalize() if t.i == sent.start else w.lower() if t.text.islower() else w
            out.append(w + t.whitespace_)
        else:
            out.append(t.text_with_ws)
    if strict and (changed < 3 or changed < 2 * content / 3):
        return None
    return "".join(out).strip() if changed >= 2 else None


def noise(sent, words, rng):
    kind = rng.choice(["shuffled", "shuffled", "random-words", "mash"])
    if kind == "shuffled":
        w = sent.text.rstrip(".!?").split()
        for _ in range(5):
            rng.shuffle(w)
            if " ".join(w) != sent.text.rstrip(".!?"):
                break
        return " ".join(w) + rng.choice([".", ""])
    if kind == "random-words":
        return " ".join(rng.choice(words) for _ in range(rng.randint(5, 16))) + rng.choice([".", ""])
    return " ".join("".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(2, 9))) for _ in range(rng.randint(4, 12)))


def main(out, strict, made_up):
    rng = random.Random(7)
    nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
    sents = sentences(nlp, rng)
    by = {"train": [], "tune": [], "held": []}
    for src, s in sents:
        by[split(s.text)].append((src, s))
    os.makedirs(out, exist_ok=True)
    for part, items in by.items():
        pool, words = {}, []
        for _, s in items:
            for t in s:
                if t.pos_ in SWAP and t.text.isalpha():
                    pool.setdefault(t.tag_, {}).setdefault(_, []).append(t.text)
                if t.text.isalpha():
                    words.append(t.text.lower())
        rng.shuffle(items)
        n, rows = PER_CLASS[part], []
        for src, s in items[:n]:
            rows.append({"label": 2, "kind": "meaning", "source": src, "text": typed(s.text.strip(), rng)})
        made = 0
        for src, s in items:
            if made == n:
                break
            fake = made_up and made % 3 == 0
            t = swapped(s, pool, rng, strict, fake, src)
            if t and not vegan.ANIMAL.search(vegan.ALLOWED.sub("", t)):
                rows.append({"label": 1, "kind": "invented" if fake else "swapped", "source": src, "text": typed(t, rng)}); made += 1
        for src, s in items[-n:]:
            t = noise(s, words, rng)
            if not vegan.ANIMAL.search(vegan.ALLOWED.sub("", t)):
                rows.append({"label": 0, "kind": "noise", "source": src, "text": typed(t, rng)})
        rng.shuffle(rows)
        with open(os.path.join(out, f"{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        print(part, len(items), "sentences,", len(rows), "rows,", {k: sum(r["label"] == k for r in rows) for k in (0, 1, 2)}, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], "--strict" in sys.argv, "--invented" in sys.argv)
