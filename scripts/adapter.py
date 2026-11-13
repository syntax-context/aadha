#!/usr/bin/env python3
"""Adapters on the frozen base, each a reader for one kind of writing that the writer names (31 October 2026, his words: "build router + adapter for
ETS, PERSUADE + Hinglish + analogies/metaphors/idioms", "make current model able to load adapters").

The base is soup $ARM (i7 at first; i8 and i9 carry the fourth mark) and does not move. Each adapter is LoRA (rank 8, on the
attention's query and value), trained only on its own rows, data-ad-<name>/, three seeds from one starting point (set under seed 0,
as train.py does for the head, so the seeds can be put together) and made into one soup: the three LoRA corrections averaged
exactly, by setting the three (A, B) pairs side by side as one adapter of rank 24 with the same alpha, so that the scale alpha/r
turns the sum of the three corrections into their mean. Rows with "source": "base" (or "i7", built before 31 October, 16:00) are the
base's own, mixed in so an adapter does not forget what the base knows.

The head, HEAD=trained or HEAD=frozen (1 November 2026, his word: "find a fix to make adapters work - fix it"). Trained, the adapter
carries its own fully retrained copy of the marking head, and every adapter built that way on i8 and i9 did its own job and moved
the base's marks everywhere else (held-b: plain −5, figurative −52, hinglish −56, reflect −67; lesson 13z69). Frozen, the base's
head stays as it is and the adapter can only move how a sentence is read before the head sees it. Runs and bundles of the frozen
kind are named -frozen-head.

There is no router (1 November 2026): one that chose a reader by itself failed three ways on i9 (lessons 13z69, 13z72); the writer
names the kind of writing and that adapter reads the piece (serve.py's "route"). The router code is kept in scripts/archive/.

usage (from the project folder; ARM and HEAD in the environment):
  python adapter.py --train <name> --seed 7      one seed
  python adapter.py --soup <name>                seeds 7, 1, 2 as one adapter
  python adapter.py --measure <name>             base + this adapter reading every sentence, on every fixed set (train.py's measure)
  python adapter.py --bundle <name> [<name> ...] copy these soups into runs/adapters-$ARM/, the folder serve.py reads (AADHA_ADAPTERS)
"""
import json, os, shutil, sys
import torch

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))
os.environ.setdefault("ARM", "i7")   # the base the adapters sit on; train.py's measure tunes on its rows
import train as T

HEAD = os.environ.get("HEAD", "trained")
# BASE_ARM (3 November 2026, his yes to a reflect adapter on soup o4x3): the soup the adapter sits on, when it is not the arm whose loader
# labels the rows. ARM keeps naming the loader and the tuning rows (train.py); an arm named o... would apply Claude's read and drop
# reflect's good-noise rows, so a reflect for o4x3 runs with ARM=hiskeys-o4x3 (his keys, as reflect1 had) and BASE_ARM=o4x3.
# Unset, BASE_ARM is ARM, and everything is as it was.
BASE_ARM = os.environ.get("BASE_ARM", os.environ["ARM"])
BASE = os.path.join(HERE, f"runs/{BASE_ARM}/soup")
TAG = ("" if BASE_ARM == "i7" else f"-{BASE_ARM}") + ("" if HEAD == "trained" else f"-{HEAD}-head")
# ADAPTER_HOME (4 November 2026, his word: "move all gagar files to its own folder"): the folder that holds an adapter's rows (data-ad-<name>/)
# and runs (runs/ad-<tag>/<name>/), when it is not this one. gagar's are in syntax/gagar-mein-sagar/. Unset, everything is as it was.
HOME = os.environ.get("ADAPTER_HOME", HERE)
RUNS = os.path.join(HOME, "runs/ad" + TAG)   # one folder per base and kind of head
BUNDLE = os.path.join(HOME, "runs/adapters" + TAG)
device = T.device


def rows(name, part):
    return T.rows(os.path.join(HOME, f"data-ad-{os.environ.get('ROWS', name)}/{part}.jsonl"))   # ROWS names another rows folder for the same adapter name (3 November 2026: reflect on o4x3 from data-ad-reflect-o4x3)


def base_model():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    return AutoModelForSequenceClassification.from_pretrained(BASE), AutoTokenizer.from_pretrained(BASE)


def train(name, seed):
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import Trainer, TrainingArguments, set_seed
    from datasets import Dataset
    model, tok = base_model()
    r = rows(name, "train")
    data = Dataset.from_dict({"text": [x["text"] for x in r], "label": [x["label"] for x in r]}) \
        .map(lambda b: tok(b["text"], truncation=True, max_length=int(os.environ.get("MAX_LENGTH", 96))), batched=True)   # MAX_LENGTH: 512 for the whole-text reader, 4 November 2026
    set_seed(0)
    # LORA_R, LORA_ALPHA, LORA_TARGETS, EPOCHS (5 November 2026, gagar's `step`): a freer or longer recipe for one adapter. Unset, everything is as it was.
    lora = dict(r=int(os.environ.get("LORA_R", 8)), lora_alpha=int(os.environ.get("LORA_ALPHA", 16)), lora_dropout=0.1, target_modules=os.environ.get("LORA_TARGETS", "query,value").split(","))
    # SEQ_CLS makes the adapter carry its own trainable copy of the head; with no task type the head stays the base's, frozen
    model = get_peft_model(model, LoraConfig(task_type=TaskType.SEQ_CLS, **lora) if HEAD == "trained" else LoraConfig(**lora))
    set_seed(seed)
    epochs = int(os.environ.get("EPOCHS", 3))
    steps = len(r) * epochs // 16
    args = TrainingArguments(output_dir=os.path.join(RUNS, name, f"ckpt-{seed}"), num_train_epochs=epochs, per_device_train_batch_size=16,
                             learning_rate=2e-4, warmup_steps=steps // 10, seed=seed, save_strategy="no", logging_steps=500, report_to=[])
    Trainer(model=model, args=args, train_dataset=data, processing_class=tok).train()
    model.save_pretrained(os.path.join(RUNS, name, f"seed-{seed}"))


def soup(name):
    from safetensors.torch import load_file, save_file
    parts = [os.path.join(RUNS, name, f"seed-{s}") for s in (7, 1, 2)]
    states = [load_file(os.path.join(p, "adapter_model.safetensors")) for p in parts]
    out = os.path.join(RUNS, name, "soup")
    shutil.copytree(parts[0], out, dirs_exist_ok=True)
    def one(k):
        t = [s[k].float() for s in states]
        return torch.cat(t, 0) if "lora_A" in k else torch.cat(t, 1) if "lora_B" in k else sum(t) / 3   # A: (r, in), B: (out, r); a head copy: averaged
    save_file({k: one(k).contiguous() for k in states[0]}, os.path.join(out, "adapter_model.safetensors"))
    conf = json.load(open(os.path.join(out, "adapter_config.json")))
    conf["r"] *= 3   # alpha stays, so the scale alpha/r is a third of a seed's: the sum of the three corrections becomes their mean
    json.dump(conf, open(os.path.join(out, "adapter_config.json"), "w"), indent=2)
    print(out)


def merged(name, path):
    """Base + adapter as one ordinary model, so train.py's measure reads it unchanged."""
    from peft import PeftModel
    model, tok = base_model()
    model = PeftModel.from_pretrained(model, path).merge_and_unload()
    out = os.path.join(RUNS, name, "merged")
    model.save_pretrained(out); tok.save_pretrained(out)
    return out


def bundle(names):
    shutil.rmtree(BUNDLE, ignore_errors=True); os.makedirs(BUNDLE)
    for name in names:
        shutil.copytree(os.path.join(RUNS, name, "soup"), os.path.join(BUNDLE, name))
        open(os.path.join(BUNDLE, name, "WEIGHTS"), "w").write(f"{name}1")
    print(BUNDLE, names)


if __name__ == "__main__":
    a = sys.argv
    if "--train" in a:
        train(a[a.index("--train") + 1], int(a[a.index("--seed") + 1]))
    elif "--soup" in a:
        soup(a[a.index("--soup") + 1])
    elif "--bundle" in a:
        bundle(a[a.index("--bundle") + 1:])
    elif "--measure" in a:
        name = a[a.index("--measure") + 1]
        T.RUNS = os.path.join(RUNS, name)
        T.measure(merged(name, os.path.join(RUNS, name, "soup")))
