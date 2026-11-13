#!/usr/bin/env python3
"""The ID10M idiom sentences and their literal twins, shared by idiommark.py (the base) and figurative.py (the adapter).

Soup i8 (31 October 2026) read plain story as common coin: 428 of 3,000 PERSUADE test lines, 53 of held-b's 1,500 meaning rows, which
hold no idiom at all (lesson 13z66). Its idiom rows were ID10M sentences (3) with swapped-word twins (0) and nothing in the same form
marked story, so the mark fastened on the form of the sentence, not on the idiom in it (lesson 13z62, for a mark instead of a kind).
So each sampled sentence gets a literal twin: the same sentence with the idiom replaced by its plain meaning, written by the local
model (Qwen3-30B-A3B-Instruct-2507, open weights, vLLM at localhost:8000) and checked in code: the idiom is gone, at least seven in
ten of the other words are kept, the length is within 0.7 to 1.6 of the original. A twin that fails is left null and no row is made.
ID10M (Tedeschi and others, 2022, CC BY-NC-SA 4.0), English; sentences of 5 to 40 words holding a tagged idiom, no editors' brackets.
usage: python literal.py   (reads sources/id10m/, writes data-id10m/{train,tune,held}.jsonl: {"text", "idiom", "literal"})
"""
import glob, json, os, random, re, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "data-id10m")
MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507"
PARTS = {"train": ("train", 4000), "tune": ("dev", 500), "held": ("test", 500)}


def id10m(name):
    """[(sentence, its first tagged idiom)] for sentences of 5 to 40 words, put back together from the token file."""
    out, toks, tags = [], [], []
    for line in open(os.path.join(HERE, f"sources/id10m/resources/bio_format/english/{name}_english.tsv"), encoding="utf-8"):
        if "\t" in line:
            t, g = line.rstrip("\n").rsplit("\t", 1)
            toks.append(t if t.endswith(" ") else t + " "); tags.append(g)
        if "\t" not in line or t.strip() in {".", "!", "?"}:
            s = re.sub(r"\s+([,.;:!?’'])", r"\1", "".join(toks)).strip()
            span = [t for t, g in zip(toks, tags) if "IDIOM" in g]
            if span and 5 <= len(s.split()) <= 40 and not re.search(r"[\[\]]", s):
                out.append((s, re.sub(r"\s+([,.;:!?’'])", r"\1", "".join(span)).strip()))
            toks, tags = [], []
    return list(dict.fromkeys(out))


def words(s):
    return re.findall(r"[a-z0-9']+", s.lower())


def twin(s, idiom):
    prompt = (f'Here is a sentence that holds the idiom "{idiom}":\n{s}\nWrite the sentence again with the idiom replaced by its plain '
              "meaning, in the same tense and person. Change nothing else. Answer with the sentence only.")
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 120, "temperature": 0}
    try:
        req = urllib.request.Request("http://localhost:8000/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
        out = json.load(urllib.request.urlopen(req, timeout=300))["choices"][0]["message"]["content"].strip().strip('"').strip()
    except (ValueError, KeyError, OSError):
        return None
    if "\n" in out or not out or idiom.lower() in out.lower():
        return None
    rest, got = words(s.replace(idiom, " ", 1)), words(out)
    kept = sum(1 for w in rest if w in got)
    long = [w for w in words(idiom) if len(w) > 2]
    if kept < 0.7 * len(rest) or sum(w in got for w in long) > len(long) // 2 or not 0.7 * len(words(s)) <= len(got) <= 1.6 * len(words(s)):
        return None
    return out


def main():
    rng = random.Random(89)
    tests = {json.loads(l)["text"] for f in glob.glob(os.path.join(HERE, "tests/**/*.jsonl"), recursive=True) for l in open(f) if l.strip()}
    made = {json.loads(l)["text"] for p in ("train", "tune", "held") for l in open(os.path.join(HERE, f"data-i7/{p}.jsonl"))}
    os.makedirs(OUT, exist_ok=True)
    for part, (split, n) in PARTS.items():
        pool = [(s, i) for s, i in id10m(split) if s not in tests and s not in made]
        pick = rng.sample(pool, min(len(pool), n))
        with ThreadPoolExecutor(32) as ex:
            lits = list(ex.map(lambda x: twin(*x), pick))
        with open(os.path.join(OUT, f"{part}.jsonl"), "w") as f:
            f.writelines(json.dumps({"text": s, "idiom": i, "literal": t}) + "\n" for (s, i), t in zip(pick, lits))
        print(f"data-id10m/{part}.jsonl: {len(pick)} idiom sentences of {len(pool)} in the pool, {sum(t is not None for t in lits)} literal twins kept")


if __name__ == "__main__":
    main()
