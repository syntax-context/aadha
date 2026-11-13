#!/usr/bin/env python3
"""Each candidate's results beside the live soup's, set by set, by the rule for going live (next-training-scope.md):
rights on the present-mark sets and the newest tester test, story read as noise, the 23 poetic nonsense lines, and held-b against
the live soup (no more than 10 rows below). The rule is his; this only lays the counts side by side.
usage: python compare.py runs/i7/soup-results-fixed.json <candidate results> ..."""
import json, sys

PRESENT = ["hand9", "hand10", "hand12", "hand13", "hand14", "probe", "blind_i3", "tester_after_i4", "persuade_test"]
res = [json.load(open(f)) for f in sys.argv[1:]]
names = ["/".join(dict.fromkeys(x for x in f.replace("runs/", "").replace("-results-fixed.json", "").split("/") if x not in ("merged", "soup"))) for f in sys.argv[1:]]


def right(r, s):
    return r[s]["no_threshold"]["right"] if s in r else None


def story_as_noise(r, s):
    c = r[s]["no_threshold"]["confusion"]
    return c[2][0] + c[2][1]


print(f"{'set':<16}" + "".join(f"{n:>18}" for n in names))
for s in PRESENT + ["held", "held_c"]:
    if s in res[0]:
        n = sum(res[0][s]["no_threshold"][k] for k in ("right", "wrong", "none"))
        print(f"{s + ' /' + str(n):<16}" + "".join(f"{right(r, s):>18}" for r in res))
print(f"{'present total':<16}" + "".join(f"{sum(right(r, s) or 0 for s in PRESENT if s in res[0]):>18}" for r in res))
print(f"{'story as noise':<16}" + "".join(f"{sum(story_as_noise(r, s) for s in PRESENT if s in r):>18}" for r in res))
print(f"{'held-b vs live':<16}" + "".join(f"{right(r, 'held') - right(res[0], 'held'):>+18}" for r in res))
for s in ("tester_after_i4", "persuade_test"):
    print(f"\n{s}, right by kind:")
    for k in res[0][s]["by_kind"]:
        print(f"  {k:<20}" + "".join(f"{r[s]['by_kind'].get(k, 0):>18}" for r in res))
