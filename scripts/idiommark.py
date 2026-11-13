#!/usr/bin/env python3
"""Arm i8 (31 October 2026): a fourth mark, 3, for a common, stock idiom. His words, 15:24: "idioms which are common and being
considered a story now - need to considered of some kind of value between good noise and story. they are not good noise. but not bad
noise either. and not plain story either"; then, from options put to him: aadha gives the mark itself, and in the balance each such
sentence counts as half a sentence of the good noise (a setting on the page). Its name, his choice at 17:50: common coin.
So the arm is arm i7's rows with:
  idiom-np        2 -> 3   the stock phrase where a metaphor would stand (sharpen.py), now the idiom mark
  id10m-idiom        3     sentences holding a tagged idiom, ID10M English (CC BY-NC-SA 4.0), from data-id10m/ (literal.py)
  id10m-literal      2     their literal twins, the same sentence with the idiom said plainly (arm i9, 31 October, 21:30)
  id10m-swapped      0     their swapped-word twins (twins.py), so the idiom's sentence form is not itself the mark (13z62)
Arm i8 had no literal twins and read plain story as common coin: 428 of 3,000 PERSUADE test lines, 53 of held-b's 1,500 meaning rows,
which hold no idiom (lesson 13z66). Arm i9 adds them and changes nothing else.
The test sets' idiom lines (hand-v9, v12, v13, kind "idiom") and a tester's two idiom corrections in tester-after-i4 were re-keyed to 3
on 31 October at 15:27, in tests/rekeyed/ and tests/tester-after-i4.jsonl, the earlier keys kept beside them as "key_before_i8";
running again moves nothing.
usage: ARM=i9 python idiommark.py   (reads data-i7/ and data-id10m/, writes data-$ARM/; spaCy, for twins.py)
"""
import collections, glob, json, os, random, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARM = os.environ.get("ARM", "i9")
MORE_IDIOMS = ("spark a chain reaction", "off to the races")


def main():
    rng = random.Random(89)
    os.makedirs(os.path.join(HERE, f"data-{ARM}"), exist_ok=True)
    for part in ("train", "tune", "held"):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-i7/{part}.jsonl"))]
        rows = [{**r, "label": 3} if r["kind"] == "idiom-np" else r for r in rows]
        idi = [json.loads(l) for l in open(os.path.join(HERE, f"data-id10m/{part}.jsonl"))]
        rows += [{"label": 3, "kind": "id10m-idiom", "source": "id10m", "text": r["text"]} for r in idi]
        rows += [{"label": 2, "kind": "id10m-literal", "source": "id10m", "text": r["literal"]} for r in idi if r["literal"]]
        # no swapped-word twins from 1 November 2026 (his rules sheet, rule 2: unwanted only if meaningless, which takes a reader); i8's and
        # i9's rows, built with them, stand
        rng.shuffle(rows)
        with open(os.path.join(HERE, f"data-{ARM}/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        print(f"data-{ARM}/{part}.jsonl: {len(rows)} rows; by mark", dict(sorted(collections.Counter(r["label"] for r in rows).items())),
              "; added", collections.Counter(r["kind"] for r in rows if r["kind"].startswith("id10m")))
    for f in glob.glob(os.path.join(HERE, "tests/rekeyed/hand-v*.jsonl")) + [os.path.join(HERE, "tests/tester-after-i4.jsonl")]:
        rows = [json.loads(l) for l in open(f) if l.strip()]
        moved = 0
        for r in rows:
            if (r.get("kind") == "idiom" or any(h in r["text"] for h in MORE_IDIOMS)) and r["label"] != 3:
                r["key_before_i8"], r["label"] = r["label"], 3; moved += 1
        if moved:
            with open(f, "w") as out:
                out.writelines(json.dumps(r) + "\n" for r in rows)
            print(f"{os.path.relpath(f, HERE)}: {moved} lines re-keyed to 3")


if __name__ == "__main__":
    main()
