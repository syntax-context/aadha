#!/usr/bin/env python3
"""The sentence reader: MiniLM with a new three-way head (0 noise, 1 grammar without sense, 2 meaning), on the recipe of the
argument notation's classifiers: three passes at 5e-5, batch 16, one starting head for every seed (set under seed 0, lesson 13z41),
seeds 7, 1 and 2, averaged into one soup.
usage: ARM=a python train.py --seed 7 | --soup | --measure <model dir>
ARM names the rows (data-<arm>/) and the runs (runs/<arm>/); with no ARM, data/ and runs/ (the first run). Every model is measured
on the same fixed sets: data-b/held.jsonl (every kind of row, its sentences in no arm's training), data-c/held.jsonl (the same
with poetic nonsense added) and the three hand sets (hand-v3: the test texts, keyed before arm C trained).
"""
import json, os, re, sys
import torch

BASE = "microsoft/MiniLM-L12-H384-uncased"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARM = os.environ.get("ARM", "")
DATA = "data-" + ARM if ARM else "data"
RUNS = os.path.join(HERE, "runs", ARM)
sys.path.insert(0, os.path.join(HERE, "scripts"))
from keys import keyed, read1, read_components, read_own, redefined
KEYS = keyed()   # his keys (grounding/keys.jsonl, scripts/keys.py), applied to every row read
RE = redefined()   # lines read again under the definitions of 2 November: a story row read as the good noise becomes the good noise
TEMPLATE = read_components()   # template lines read under his components rule: X trains as unwanted noise, I as common coin (from arm i13)
READ = read1()   # the good-noise rows Claude Code has read and kept (grounding/read-1.jsonl); once it exists, an unread or refused one is dropped
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"   # mps: the Mac, 2 November 2026, when the shared training machine ran at 3 steps a second


OWN, OWN_HELD = read_own() if ARM.startswith("o") else (None, None)


def own_rows(name, out):
    """Arms named o...: Claude's own reading replaces every label it covers. In training, a read line held out for testing is left out, and so is an unread row of a kind that needed reading. A data folder holding a BAKED file (own/rows.py wrote it) carries final labels and is trained as it stands. An arm name ending x<n> sees every good-noise row n times."""
    baked = os.path.exists(os.path.join(HERE, DATA, "BAKED"))
    if not baked:
        for r in out:
            r["label"] = OWN.get(r["text"], r["label"])
    if name.startswith(("tests/", "own/")):
        for r in out:
            r["label"] = OWN.get(r["text"], r["label"])
        return out
    kept = out if baked else [r for r in out if r["text"] not in OWN_HELD and (r["text"] in OWN or (r["label"] != 1 and r.get("kind") != "id10m-idiom"))]
    m = re.search(r"x(\d+)$", ARM)
    if m and name.endswith("train.jsonl"):
        kept += [r for r in kept if r["label"] == 1] * (int(m.group(1)) - 1)
    return kept


def rows(name):
    """The rows of a file, with his keys applied: a sentence he has keyed (grounding/keys.jsonl, scripts/keys.py) carries his key,
    whatever the row said, and the row's own label beside it as key_before (1 November 2026, his word: every training job rests on
    his keying)."""
    out = [json.loads(l) for l in open(os.path.join(HERE, name))]
    if OWN is not None:
        return own_rows(name, out)
    for r in out:
        k = KEYS.get(r["text"])
        if k is not None and r["label"] != k:
            r["key_before"], r["label"] = r["label"], k
    if os.path.exists(os.path.join(HERE, os.path.dirname(name), "BAKED")) and not name.startswith("tests/"):   # 3 November 2026: a folder whose labels are final (own/reflect-rows.py wrote it) is trained as it stands, his keys applied and nothing else
        return out
    if not name.startswith("tests/"):   # training rows only; a test row carries only his key
        for r in out:
            if r["label"] == 2 and r["text"] not in KEYS and RE.get(r["text"]) == "N":
                r["key_before"], r["label"] = 2, 1
            if r["label"] == 1 and r["text"] not in KEYS and TEMPLATE.get(r["text"]) in ("X", "I"):
                r["key_before"], r["label"] = 1, {"X": 0, "I": 3}[TEMPLATE[r["text"]]]
    if READ and not name.startswith("tests/"):   # training rows only: a good-noise row stands only once read and kept (his key wins over the reading)
        n = len(out)
        out = [r for r in out if r["label"] != 1 or r["text"] in KEYS or READ.get(r["text"])]
        if n != len(out):
            print(f"{name}: {n - len(out)} good-noise rows not read or not kept, dropped")
    return out


def train(seed):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments, set_seed
    from datasets import Dataset
    tok = AutoTokenizer.from_pretrained(BASE)
    r = rows(f"{DATA}/train.jsonl")
    data = Dataset.from_dict({"text": [x["text"] for x in r], "label": [x["label"] for x in r]}) \
        .map(lambda b: tok(b["text"], truncation=True, max_length=96), batched=True)
    set_seed(0)
    model = AutoModelForSequenceClassification.from_pretrained(BASE, num_labels=1 + max(x["label"] for x in r))   # 4 from arm i8: 3, the idiom mark
    set_seed(seed)
    args = TrainingArguments(output_dir=os.path.join(RUNS, f"ckpt-{seed}"), num_train_epochs=3, per_device_train_batch_size=16,
                             learning_rate=5e-5, warmup_steps=675,   # a tenth of 36,000 rows x 3 passes / 16; transformers 5 has no warmup_ratio
                             seed=seed, save_strategy="no", logging_steps=500, report_to=[])
    prior = os.path.join(HERE, DATA, "PRIOR-WEIGHTS.json")   # 4 November 2026: own/hold-prior.py, so that adding rows does not change how readily a mark is used
    m = re.match(r"o(\d+)", ARM)
    if m and int(m.group(1)) >= 7 and not os.path.exists(prior):
        sys.exit(f"{prior} is missing: run own/hold-prior.py first")
    trainer = Trainer
    if os.path.exists(prior):
        loaded = json.load(open(prior))
        weight = torch.tensor([loaded[str(i)] for i in range(len(loaded))], dtype=torch.float)

        class trainer(Trainer):
            def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
                labels = inputs.pop("labels")
                out = model(**inputs)
                loss = torch.nn.functional.cross_entropy(out.logits, labels, weight=weight.to(out.logits.device))
                return (loss, out) if return_outputs else loss
    trainer(model=model, args=args, train_dataset=data, processing_class=tok).train()
    model.save_pretrained(os.path.join(RUNS, f"seed-{seed}")); tok.save_pretrained(os.path.join(RUNS, f"seed-{seed}"))


def soup():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    parts = [os.path.join(RUNS, f"seed-{s}") for s in (7, 1, 2)]
    states = [AutoModelForSequenceClassification.from_pretrained(p).state_dict() for p in parts]
    model = AutoModelForSequenceClassification.from_pretrained(parts[0])
    model.load_state_dict({k: sum(s[k].float() for s in states) / 3 if states[0][k].is_floating_point() else states[0][k] for k in states[0]})
    model.save_pretrained(os.path.join(RUNS, "soup")); AutoTokenizer.from_pretrained(parts[0]).save_pretrained(os.path.join(RUNS, "soup"))


def predict(path, r):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tok, model = AutoTokenizer.from_pretrained(path), AutoModelForSequenceClassification.from_pretrained(path).to(device).eval()
    out = []
    for i in range(0, len(r), 128):
        enc = tok([x["text"] for x in r[i:i + 128]], truncation=True, max_length=96, padding=True, return_tensors="pt").to(device)
        with torch.no_grad():
            p = model(**enc).logits.softmax(-1)
        out += [(int(x.argmax()), float(x.max())) for x in p]
    return out


def count(r, answers):
    c = {"right": 0, "wrong": 0, "none": 0, "confusion": [[0] * 4 for _ in range(4)]}   # four marks from arm i8
    for x, a in zip(r, answers):
        if a is None:
            c["none"] += 1
        else:
            c["right" if a == x["label"] else "wrong"] += 1; c["confusion"][x["label"]][a] += 1
    return c


def measure(path):
    """No threshold, and the threshold that makes no wrong answer on the tuning half; then the held half and the hand set."""
    tune = rows(f"{DATA}/tune.jsonl")
    pt = predict(path, tune)
    best = (-1, 1.0)
    for t in [x / 100 for x in range(34, 100)] + [0.995, 0.998, 0.999]:
        c = count(tune, [a if p >= t else None for a, p in pt])
        if c["wrong"] == 0 and c["right"] > best[0]:
            best = (c["right"], t)
    t = best[1]
    res = {"model": path, "threshold": t}
    # From 30 October 2026, 13:05 every set is the re-keyed copy (scripts/rekey.py): 2 story, 1 desirable noise, 0 undesirable noise.
    sets = [("held", "tests/rekeyed/held-b.jsonl"), ("held_c", "tests/rekeyed/held-c.jsonl")] + [(f"hand{n if n > 1 else ''}", f"tests/rekeyed/hand-v{n}.jsonl") for n in [*range(1, 11), 12, 13, 14]] + [("probe", "tests/probe-i.jsonl"), ("blind_i3", "tests/blindspots-i3.jsonl")]   # hand-v11 archived with the cummings thread (14:05)
    if OWN is not None:
        sets += [("own_held", "own/held.jsonl"), ("own_tests", "own/tests.jsonl")]
    sets += [(n, f) for n, f in [("tester_after_i4", "tests/tester-after-i4.jsonl"), ("persuade_test", "tests/persuade-test.jsonl"), ("hinglish_test", "tests/hinglish-test.jsonl"), ("prose", "tests/prose.jsonl")] if os.path.exists(os.path.join(HERE, f))]   # 31 Oct: the adapters' tests
    for name, f in sets:
        r = rows(f); p = predict(path, r)
        res[name] = {"no_threshold": count(r, [a for a, _ in p]), "at_threshold": count(r, [a if q >= t else None for a, q in p]),
                     "by_kind": {k: sum(a == x["label"] for x, (a, _) in zip(r, p) if x["kind"] == k) for k in sorted({x["kind"] for x in r})},
                     "as_noise_or_story": sum((a == 2) == (x["label"] == 2) for x, (a, _) in zip(r, p))}   # 0 and 1 both noise (15:38)
        if not name.startswith("held"):
            res[name + "_misses"] = [{"key": x["label"], "said": a, "p": round(q, 3), "text": x["text"]} for x, (a, q) in zip(r, p) if a != x["label"]]
    json.dump(res, open(os.path.join(RUNS, os.path.basename(path) + "-results-fixed.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if not k.endswith("_misses")}, indent=1))


if __name__ == "__main__":
    if "--seed" in sys.argv:
        train(int(sys.argv[sys.argv.index("--seed") + 1]))
    elif "--soup" in sys.argv:
        soup()
    else:
        measure(sys.argv[sys.argv.index("--measure") + 1])
