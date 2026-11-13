#!/usr/bin/env python3
"""Rows for the *reflect* adapter (next-training-scope.md, Plug-in 3): analogy and layered meaning inside argued, reflective prose.
Source: the ETS University Coursework Writing Corpus (Educational Testing Service, CC BY-NC-SA 4.0), sources/ets/.

Three steps, on the training machine, with a local model served by vLLM at localhost:8000 (Qwen3-30B-A3B-Instruct-2507, open weights):
  --sort      every ETS sentence of five words or more is shown to the model with the page's own definitions; the model answers
              with one digit (1 story, 2 good noise, 3 unwanted noise) and nothing else, capped at one token; code keeps an answer
              only when the model gave that digit at least 0.9 of its probability, otherwise the sentence is "don't know" and not used.
  --replicas  for each sentence kept as good noise, the model writes a replica (a new subject and new words, the same register,
              length and kind of analogy) and its plain twin (the same replica with the analogy said plainly), as training rows that no
              person reads. Code drops a replica sharing five words in a row with any ETS sentence, or far from its source's length.
              A replica is an adaptation of an ETS passage, so ShareAlike reaches it: CC BY-NC-SA 4.0.
  --build     rows, split by essay: ETS good noise (1) and ETS story from the same essays (2), replicas (1) and their twins (2),
              shuffled and swapped twins of ETS story (0, lessons 13z62 and 13z65), the base's own rows (data-$ARM/, "source": "base"); and grounding/reflect-check-100.jsonl,
              100 rows drawn from what the model sorted or wrote, for his keys. The adapter goes live only if his keys agree on 85.
usage: python reflect.py --sort | --replicas | --build
"""
import collections, glob, json, math, os, random, re, sys, urllib.request
from keys import keyed, read1   # his keys and Claude Code's reading (1 November 2026, grounding/rules-keys.txt): rows that must be read enter only once read

KEYS, READ = keyed(), read1()

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "data-ad-reflect")
MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507"
RULES = """Story is plain writing: real-world acts, who did what, and when. An everyday idiom, such as "the office was an oven by two", is story too. Made-up writing is story too when it is told plainly, including things that cannot happen, such as "at midnight the clock began to speak".
The good noise has a rational, philosophical or explainable meaning, more than a report has room for. An analogy or a metaphor counts when it carries such a meaning; one that is just verbiage, a verbal embellishment, is unwanted noise. "A queue is a promise that strangers make to each other without speaking" means something, but more than a report has room for, so it is good noise. An analogy inside an argument ("they are like the keystone in an arch") is good noise.
Unwanted noise is gibberish (shuffled words, letters at random) and nonsense with no meaning under it, such as "A blue arithmetic slept inside the echo of the stairs"."""


def ask(messages, max_tokens, logprobs=False):
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0}
    if logprobs:
        body.update(logprobs=True, top_logprobs=5)
    req = urllib.request.Request("http://localhost:8000/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=300))["choices"][0]


def ets():
    """(essay, index, sentence) for every sentence of five words or more."""
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, "sources/ets/writing-samples/*.txt"))):
        ss = [s.strip() for s in re.split(r"\n+|(?<=[.!?])\s+", open(f, encoding="utf-8", errors="replace").read()) if s.strip()]
        out += [(os.path.basename(f), i, s) for i, s in enumerate(ss) if 5 <= len(s.split()) <= 60]
    return out


def sort():
    from concurrent.futures import ThreadPoolExecutor
    def one(row):
        essay, i, s = row
        c = ask([{"role": "system", "content": RULES + "\nAnswer with one digit only: 1 story, 2 good noise, 3 unwanted noise."},
                 {"role": "user", "content": s}], 1, logprobs=True)
        top = {t["token"].strip(): math.exp(t["logprob"]) for t in c["logprobs"]["content"][0]["top_logprobs"]}
        d, p = max(((k, v) for k, v in top.items() if k in "123" and k), key=lambda x: x[1], default=("", 0))
        return {"essay": essay, "i": i, "text": s, "answer": d, "p": round(p, 4), "kept": p >= 0.9}
    rows = ets()
    with ThreadPoolExecutor(32) as pool:
        got = list(pool.map(one, rows))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "sorted.jsonl"), "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in got)
    print(len(got), "sentences;", collections.Counter((r["answer"], r["kept"]) for r in got))


def replicas():
    from concurrent.futures import ThreadPoolExecutor
    sorted_ = [json.loads(l) for l in open(os.path.join(OUT, "sorted.jsonl"))]
    good = [r for r in sorted_ if r["kept"] and r["answer"] == "2"]
    grams = {g for r in sorted_ for g in zip(*[r["text"].lower().split()[k:] for k in range(5)])}
    def one(r):
        prompt = ("Here is a sentence from a first-year university student's coursework. It holds an analogy or layered meaning.\n\n"
                  f"{r['text']}\n\nWrite two sentences as JSON, {{\"replica\": ..., \"plain\": ...}}. replica: a new sentence on a different "
                  "subject that a student might write in the same kind of assignment, with the same kind of analogy, about the same length, "
                  "with the same casing and punctuation habits, sharing no phrase with the original. plain: the replica with the analogy "
                  "said plainly, the same subject and about the same length. JSON only.")
        try:
            d = json.loads(ask([{"role": "user", "content": prompt}], 200)["message"]["content"])
            rep, plain = str(d["replica"]).strip(), str(d["plain"]).strip()
        except (ValueError, KeyError, TypeError):
            return None
        n = len(r["text"].split())
        if not (0.6 * n <= len(rep.split()) <= 1.5 * n) or any(g in grams for g in zip(*[rep.lower().split()[k:] for k in range(5)])):
            return None
        return {"essay": r["essay"], "source": r["text"], "replica": rep, "plain": plain}
    with ThreadPoolExecutor(32) as pool:
        got = [x for x in pool.map(one, good) if x]
    with open(os.path.join(OUT, "replicas.jsonl"), "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in got)
    print(f"{len(got)} replicas kept of {len(good)} good-noise sentences")


def shuffled(s, rng):
    w = s.split()
    rng.shuffle(w)
    return " ".join(w)


def build():
    rng = random.Random(73)
    tests = {json.loads(l)["text"] for f in glob.glob(os.path.join(HERE, "tests/**/*.jsonl"), recursive=True) for l in open(f) if l.strip()}
    sorted_ = [r for r in (json.loads(l) for l in open(os.path.join(OUT, "sorted.jsonl"))) if r["kept"] and r["text"] not in tests]
    reps = [json.loads(l) for l in open(os.path.join(OUT, "replicas.jsonl"))]
    essays = sorted({r["essay"] for r in sorted_})
    rng.shuffle(essays)
    part_of = {e: ("train" if k < 0.8 * len(essays) else "tune" if k < 0.9 * len(essays) else "held") for k, e in enumerate(essays)}
    replay = {"train": 10000, "tune": 1250, "held": 1250}
    for part in ("train", "tune", "held"):
        mine = [r for r in sorted_ if part_of[r["essay"]] == part]
        good = [r["text"] for r in mine if r["answer"] == "2"]
        reps_p = [r for r in reps if part_of.get(r["essay"]) == part]
        story_pool = [r["text"] for r in mine if r["answer"] == "1"]
        story = rng.sample(story_pool, min(len(story_pool), 2 * (len(good) + len(reps_p))))
        rows = [{"label": 1, "kind": "ets-good", "source": "ets", "text": s} for s in good]   # the model's sort: rule 4, his yes
        rows += [{"label": 2, "kind": "ets-story", "source": "ets", "text": s} for s in story]
        # a written replica is a row once read (rule 5: "no. It has to be read"): his key, or Claude Code's reading of every good-noise row
        # (his word of 1 November); its plain twin only once he has keyed it
        rows += [{"label": KEYS.get(r["replica"], 1), "kind": "replica", "source": "ets-replica", "text": r["replica"]} for r in reps_p if r["replica"] in KEYS or READ.get(r["replica"])]
        rows += [{"label": KEYS[r["plain"]], "kind": "replica-plain", "source": "ets-replica", "text": r["plain"]} for r in reps_p if r["plain"] in KEYS]
        rows += [{"label": 0, "kind": "ets-shuffled", "source": "ets", "text": shuffled(s, rng)} for s in story[:len(story) // 3]]   # rule 1, his yes
        # no swapped-word twins from 1 November (rule 2: unwanted only if meaningless, which takes a reader); rows built with them before stand
        i7 = [json.loads(l) for l in open(os.path.join(HERE, f"data-{os.environ.get('ARM', 'i7')}/{part}.jsonl"))]
        rows += [{**x, "source": "base"} for x in rng.sample(i7, replay[part])]
        rng.shuffle(rows)
        with open(os.path.join(OUT, f"{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        print(f"data-ad-reflect/{part}.jsonl: {len(rows)} rows", collections.Counter("base" if r["source"] == "base" else r["kind"] for r in rows))
    check = os.path.join(HERE, "grounding/reflect-check-100.jsonl")
    if os.path.exists(check):   # his sheet stands once drawn; a rebuild on another base does not redraw it
        return
    pick = rng.sample([{"text": r["text"], "model": {"1": 2, "2": 1, "3": 0}[r["answer"]], "from": "ets, sorted"} for r in sorted_ if r["answer"] in "12"], 60) \
        + rng.sample([{"text": r["replica"], "model": 1, "from": "replica"} for r in reps], 20) \
        + rng.sample([{"text": r["plain"], "model": 2, "from": "replica twin"} for r in reps], 20)
    rng.shuffle(pick)
    with open(check, "w") as f:
        f.writelines(json.dumps({**p, "his_key": None}) + "\n" for p in pick)
    print("grounding/reflect-check-100.jsonl: 100 rows for his keys (2 story, 1 good noise, 0 unwanted)")


if __name__ == "__main__":
    {"--sort": sort, "--replicas": replicas, "--build": build}[sys.argv[1]]()
