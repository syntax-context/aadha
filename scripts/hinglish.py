#!/usr/bin/env python3
"""Rows for the *hinglish* adapter (31 October 2026, his words: "adapter for ... Hinglish"): Romanised Hindi-English writing, with
story, the good noise and unwanted noise in the same mix. Sources, licences read at source on 31 October:
  PHINC (Srivastava and Singh, 2020, CC BY 4.0): Hinglish social-media sentences written by people. Handles, links and hashtags are
    taken out; what is left, five words or more, is story (2).
  HinGE (Srivastava and Singh, 2021, CC BY 4.0): Hinglish written by people from English sentences. Story (2).
  Neither has labelled figures, so the good noise is written by a local model (Qwen3-30B-A3B-Instruct, open weights, on the training machine,
    vLLM at localhost:8000): the Hinglish of each Fig-QA metaphor (MIT) as the good noise (1), and of its plain meaning as its twin (2).
    These are training rows no person reads; his keys on 100 of them (grounding/hinglish-check-100.jsonl) must agree on 85 before the
    adapter goes live.
Each kind has shuffled twins in its own form (0, lesson 13z62), and the base's own rows (data-$ARM/) are mixed in ("source": "base").
usage: python hinglish.py --write   (needs the model)  |  python hinglish.py --build   (writes data-ad-hinglish/)
"""
import ast, collections, csv, glob, json, os, random, re, sys, urllib.request
from keys import keyed, read1   # his keys and the Opus reading (1 November 2026)

KEYS, READ = keyed(), read1()


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "sources")
OUT = os.path.join(HERE, "data-ad-hinglish")
MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507"
REPLAY = {"train": 10000, "tune": 1250, "held": 1250}


def clean(s):
    s = re.sub(r"@\w+|https?://\S+|#\w+|\bRT\b", " ", s)
    return re.sub(r"\s+", " ", s).strip(" .:-")


def real():
    phinc = [clean(r["Sentence"]) for r in csv.DictReader(open(os.path.join(SRC, "phinc/PHINC.csv"), encoding="utf-8", errors="replace"))]
    hinge = [h.strip() for r in csv.DictReader(open(os.path.join(SRC, "hinge/HinGE.csv"), encoding="utf-8", errors="replace"))
             for h in ast.literal_eval(r["Human-generated Hinglish"] or "[]")]
    keep = lambda xs: [s for s in dict.fromkeys(xs) if 5 <= len(s.split()) <= 40]
    return keep(phinc), keep(hinge)


def write():
    from concurrent.futures import ThreadPoolExecutor
    pairs = {}
    for r in csv.DictReader(open(os.path.join(SRC, "figqa/train_l.csv"), encoding="utf-8")):
        pairs.setdefault(r["startphrase"].strip(), (r["qid"], r["ending1" if r["labels"] == "0" else "ending2"].strip()))
    def one(item):
        metaphor, (qid, meaning) = item
        prompt = ("Write these two English sentences in Hinglish, the way young people in India type it: Romanised Hindi mixed with English "
                  "words, no Devanagari. Keep the first one's figure of speech as a figure; keep the second one plain.\n"
                  f"1. {metaphor}\n2. {meaning}\nAnswer as JSON only: {{\"figure\": ..., \"plain\": ...}}")
        body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 120, "temperature": 0.7}
        try:
            req = urllib.request.Request("http://localhost:8000/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
            d = json.loads(json.load(urllib.request.urlopen(req, timeout=300))["choices"][0]["message"]["content"])
            fig, plain = str(d["figure"]).strip(), str(d["plain"]).strip()
        except (ValueError, KeyError, TypeError, OSError):
            return None
        if re.search(r"[ऀ-ॿ]", fig + plain) or fig.lower() == metaphor.lower():
            return None
        return {"qid": qid, "metaphor": metaphor, "figure": fig, "plain": plain}
    with ThreadPoolExecutor(32) as pool:
        got = [x for x in pool.map(one, pairs.items()) if x]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "written.jsonl"), "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in got)
    print(f"{len(got)} Hinglish pairs written of {len(pairs)} Fig-QA metaphors")


def shuffled(s, rng):
    w = s.split()
    rng.shuffle(w)
    return " ".join(w)


def build():
    rng = random.Random(83)
    tests = {json.loads(l)["text"] for f in glob.glob(os.path.join(HERE, "tests/**/*.jsonl"), recursive=True) for l in open(f) if l.strip()}
    phinc, hinge = real()
    written = [json.loads(l) for l in open(os.path.join(OUT, "written.jsonl"))]
    story = [("phinc", s) for s in phinc] + [("hinge", s) for s in hinge]
    story = [x for x in story if x[1] not in tests]
    rng.shuffle(story)
    qids = sorted({w["qid"] for w in written}); rng.shuffle(qids)
    part_q = {q: ("train" if k < 0.8 * len(qids) else "tune" if k < 0.9 * len(qids) else "held") for k, q in enumerate(qids)}
    cut = [0, int(len(story) * 0.8), int(len(story) * 0.9), len(story)]
    for k, part in enumerate(("train", "tune", "held")):
        st = story[cut[k]:cut[k + 1]]
        w = [x for x in written if part_q[x["qid"]] == part]
        rows = [{"label": 2, "kind": f"{src}-story", "source": src, "text": s} for src, s in st]   # rule 10, his yes
        # a written Hinglish figure is a row only once read and kept (1 November 2026, his words: "i said all good noise (1) has to be
        # read. including this"; the Opus reading, grounding/read-1.jsonl); his key wins where he has keyed it. The written plain twins
        # stay out until he keys them. No swapped-word twins (rule 2: unwanted only if meaningless, which takes a reader).
        rows += [{"label": KEYS.get(x["figure"], 1), "kind": "hinglish-figure", "source": "written", "text": x["figure"]} for x in w
                 if x["figure"] in KEYS or READ.get(x["figure"])]
        rows += [{"label": 0, "kind": "shuffled-story", "source": "phinc+hinge", "text": shuffled(s, rng)} for _, s in st[:len(st) // 3]]   # rule 1
        i7 = [json.loads(l) for l in open(os.path.join(HERE, f"data-{os.environ.get('ARM', 'i7')}/{part}.jsonl"))]
        rows += [{**x, "source": "base"} for x in rng.sample(i7, REPLAY[part])]
        rng.shuffle(rows)
        with open(os.path.join(OUT, f"{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        print(f"data-ad-hinglish/{part}.jsonl: {len(rows)} rows", collections.Counter("base" if r["source"] == "base" else r["kind"] for r in rows))
    check = os.path.join(HERE, "grounding/hinglish-check-100.jsonl")
    if os.path.exists(check):   # his sheet stands once drawn; a rebuild on another base does not redraw it
        return
    pick = rng.sample([{"text": x["figure"], "model": 1, "from": "written figure"} for x in written], 50) \
        + rng.sample([{"text": x["plain"], "model": 2, "from": "written plain"} for x in written], 50)
    rng.shuffle(pick)
    with open(check, "w") as f:
        f.writelines(json.dumps({**p, "his_key": None}) + "\n" for p in pick)
    print("grounding/hinglish-check-100.jsonl: 100 rows for his keys (2 story, 1 good noise, 0 unwanted)")


if __name__ == "__main__":
    {"--write": write, "--build": build}[sys.argv[1]]()
