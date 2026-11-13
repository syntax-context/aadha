#!/usr/bin/env python3
"""The code-only route, the bar the reader must clear (lesson 13z34): a sentence is noise when under 60 per cent of its words
are in a word list, otherwise meaning. Code alone cannot tell grammar without sense, so it never answers 1.
usage: python bar.py <rows.jsonl>"""
import json, re, sys

WORDS = {w.strip().lower() for w in open("/usr/share/dict/words") if w.strip().isalpha()}


def say(text):
    w = re.findall(r"[a-zA-Z']+", text)
    known = sum(x.lower().strip("'") in WORDS for x in w) / max(1, len(w))
    return 0 if known < 0.6 else 2


r = [json.loads(l) for l in open(sys.argv[1])]
c = [[0] * 3 for _ in range(3)]
for x in r:
    c[x["label"]][say(x["text"])] += 1
right = sum(c[i][i] for i in range(3))
print(f"{sys.argv[1]}: {right} of {len(r)} right; rows are the key (0 noise, 1 grammar without sense, 2 meaning), columns what code said: {c}")
