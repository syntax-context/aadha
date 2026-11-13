#!/usr/bin/env python3
"""Ship or archive, for each adapter (1 November 2026, his words: "find a fix for adapter use - plan use or discard and archive. i do
not want anything in limbo. next version release needs to be wioth adapters"). An adapter reads a piece only when the writer names
its kind, so it is judged on writing of its kind, against the base reading the same lines. The rule, which code applies:
  ship    the adapter reads more of its kind's lines right than the base does
  archive otherwise
Its kind's lines, from the keyed tests (rule 13, his yes):
  reflect     "An argued or reflective piece, reasoning with comparisons": the testers' reflective piece (tests/tester-after-i4.jsonl,
              one tester's 25 lines and another's one) and hand-v13's argued claims (kind "claim")
  figurative  "Writing full of figures: metaphors, similes, idioms": every hand set's layered, idiom, casual-layered and wry lines,
              and the probe set's layered and abstraction lines
  hinglish    "Hinglish: Hindi and English mixed, in English letters": tests/hinglish-test.jsonl, 80 lines he keyed (60 real Hinglish
              from PHINC and HinGE's held split, 20 written figures), from grounding/hinglish-test-keys.txt
usage: ARM=i11 python kinds.py
       BASE_ARM=o4x3 BASE_RESULTS=runs/hiskeys-o4x3/soup-results-fixed.json python kinds.py   (3 November 2026: an adapter on soup o4x3,
       judged against o4x3 measured on his keys, the same keys its adapter was measured on)"""
import json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARM = os.environ.get("BASE_ARM", os.environ.get("ARM", "i11"))
BASE_RESULTS = os.environ.get("BASE_RESULTS", f"runs/{ARM}/soup-results-fixed.json")
KIND = {"reflect": {"tester_after_i4": None, "hand13": ["claim"]},
        "figurative": {**{h: ["layered", "idiom", "casual-layered", "wry"] for h in ("hand9", "hand10", "hand12", "hand13", "hand14")},
                       "probe": ["layered", "abstraction"]},
        "hinglish": {"hinglish_test": None}}


def right(res, sets):
    n = 0
    for s, kinds in sets.items():
        n += res[s]["no_threshold"]["right"] if kinds is None else sum(res[s]["by_kind"].get(k, 0) for k in kinds)
    return n


base = json.load(open(os.path.join(HERE, BASE_RESULTS)))
for name, sets in KIND.items():
    path = os.path.join(HERE, f"runs/ad-{ARM}/{name}/merged-results-fixed.json")
    if not os.path.exists(path):
        print(f"{name}: not measured"); continue
    ad = json.load(open(path))
    if any(s not in base or s not in ad for s in sets):
        print(f"{name}: its test is not measured yet (keys not in, or measured before they were)"); continue
    b, a = right(base, sets), right(ad, sets)
    print(f"{name}: on its kind's lines the base reads {b} right, {name} reads {a}: {'SHIP' if a > b else 'ARCHIVE'}")
