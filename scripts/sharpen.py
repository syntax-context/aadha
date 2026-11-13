#!/usr/bin/env python3
"""Arm I3 (30 Oct 2026, 15:40). His words, after soup i2 went live: "so does it need to be better? can we train one more round?"
tests/hand-v13.jsonl was keyed first (15:36). On it soup i2 read all 10 idioms as story and all 10 unwanted lines as unwanted, but
caught 2 of 8 lines of the good noise said as a plain claim ("A diary is a museum of small defeats."). Its two idiom errors on
hand-v9 share one shape: an idiom standing where a metaphor would ("The exam was a piece of cake in the end."), the shape i2's
widened rows teach as good noise. So arm I3 is arm I2's rows plus:
  claims (mark 1, kind "claim"): an everyday thing said to be a store of something abstract, or something abstract in disguise;
  idioms in the metaphor's place (mark 2, kind "idiom-np"): "the paperwork was a nightmare", the stock phrase, which is story.
No content word of any hand set's good-noise lines is in the claim tables, and none of their idiom lines' in the idiom tables.
usage: python sharpen.py   (reads data-i2/, writes data-i3/)
"""
import importlib.util, json, os, random, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("poetic", os.path.join(HERE, "scripts/poetic.py")); poetic = importlib.util.module_from_spec(spec); spec.loader.exec_module(poetic)
spec = importlib.util.spec_from_file_location("vegan", poetic.VEGAN); vegan = importlib.util.module_from_spec(spec); spec.loader.exec_module(vegan)

THING = ["wedding album", "passport", "salary slip", "group chat", "escalator", "ration card", "CV", "clinic reception", "railway platform",
         "farewell speech", "magazine", "footnote", "password", "signature", "uniform", "toll booth", "recipe", "souvenir", "visiting card",
         "notice board", "lunch box", "photocopy", "laptop charger", "pension"]
STORE = ["a warehouse", "an orchestra", "a ledger", "a parade", "a cemetery", "a nursery", "a census", "an anthology", "a pharmacy",
         "a catalogue", "a ration", "an inventory", "a vault"]
STUFF = ["postponed wishes", "polite lies", "rented confidence", "unspoken grudges", "tiny surrenders", "practised greetings",
         "abandoned plans", "modest ambitions", "minor victories", "unpaid favours", "careful pretences", "half-kept vows",
         "swallowed complaints", "secondhand dreams"]
FEELING = ["fear", "pride", "regret", "deference", "vanity", "boredom", "loneliness", "guilt", "envy", "impatience", "politeness", "ambition"]
DISGUISE = ["with a stamp on it", "in an ironed kurta", "with an interest rate", "wearing a tie", "on a monthly plan", "with a receipt",
            "in a laminated cover", "with working hours", "dressed for a photograph", "with a cooling-off period"]
SHAPES = ["A {t} is {s} of {u}.", "A {t} is just {s} of {u}.", "Every {t} is {s} of {u}.", "A {t} is {f} {d}.", "Every {t} is {f} {d}."]
IDIOM = ["a nightmare", "a breeze", "a walk in the park", "a rollercoaster", "a lost cause", "a pain in the neck", "a drop in the ocean",
         "a long shot", "an eye-opener", "a red flag", "a godsend", "a game changer", "the final straw", "the tip of the iceberg",
         "a no-brainer", "a done deal", "an uphill battle", "a mixed bag"]
SUBJECT = ["the trip", "the paperwork", "the drive to Vadodara", "my first week", "the shift", "the move", "the renovation", "the wedding",
           "the audit", "the admission process", "the second semester", "the presentation", "the lab report", "the internship",
           "the visa application", "the tournament", "the rehearsal", "the parking", "the commute", "the group assignment"]
VERB = ["was", "is", "turned out to be", "has been"]
PER_PART = {"train": (4000, 1200), "tune": (500, 150), "held": (500, 150)}   # (claims, idioms); the idiom tables make 1,440
HAND = ["tests/hand-v9.jsonl", "tests/hand-v10.jsonl", "tests/hand-v12.jsonl", "tests/hand-v13.jsonl", "tests/probe-i.jsonl"]
COMMON = {"that", "their", "with", "into", "from", "like", "every", "where", "when", "they", "this", "what", "who", "only", "keeps",
          "never", "after", "before", "same", "each", "have", "keep", "open", "someone", "without", "was", "were", "had", "become",
          "the", "her", "his", "our", "my", "in", "on", "of", "a", "an", "is", "it", "its", "by", "for", "and", "to", "at", "you", "all",
          "no", "one", "already", "else", "between", "s", "both", "behind", "back", "how", "knew", "everyone", "could", "not", "she",
          "we", "us", "old", "just", "has", "been", "be", "out", "up", "i", "me", "made", "first", "small", "any", "still", "end",
          "turned", "once", "so", "had", "your"}


def words(lines):
    return {w.lower() for line in lines for w in re.findall(r"[A-Za-z]+", line)} - COMMON


def overlap(hand, tables):
    seen, have = words(hand), words(tables)
    return seen & (have | {w + "s" for w in have} | {w[:-1] for w in have if w.endswith("s")})


def claim(rng):
    s = rng.choice(SHAPES).format(t=rng.choice(THING), s=rng.choice(STORE), u=rng.choice(STUFF), f=rng.choice(FEELING), d=rng.choice(DISGUISE))
    return re.sub(r"^A ([aeiouAEIOU])", r"An \1", s)


def idiom(rng):
    s = f"{rng.choice(SUBJECT)} {rng.choice(VERB)} {rng.choice(IDIOM)}."
    return s[:1].upper() + s[1:]


def main():
    hand = [json.loads(l) for f in HAND for l in open(os.path.join(HERE, f))]
    bad = overlap([r["text"] for r in hand if r["label"] == 1], THING + STORE + STUFF + FEELING + DISGUISE + SHAPES)
    assert not bad, f"words of the hand sets' good-noise lines are in the claim tables: {sorted(bad)}"
    bad = overlap([r["text"] for r in hand if r["kind"] == "idiom"], IDIOM + SUBJECT + VERB)
    assert not bad, f"words of the hand sets' idiom lines are in the idiom tables: {sorted(bad)}"
    rng, made = random.Random(53), set()
    os.makedirs(os.path.join(HERE, "data-i3"), exist_ok=True)
    for part in ("train", "tune", "held"):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-i2/{part}.jsonl"))]
        made |= {r["text"] for r in rows}
        added = []
        for make, label, kind, n in ((claim, 1, "claim", PER_PART[part][0]), (idiom, 2, "idiom-np", PER_PART[part][1])):
            got, tries = 0, 0
            while got < n and tries < 2000000:
                tries += 1
                s = make(rng)
                if s in made or vegan.ANIMAL.search(vegan.ALLOWED.sub("", s)):
                    continue
                made.add(s); got += 1
                added.append({"label": label, "kind": kind, "source": "sharpen.py", "text": poetic.typed(s, rng)})
        out = rows + added
        rng.shuffle(out)
        with open(os.path.join(HERE, f"data-i3/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in out)
        print(f"data-i3/{part}.jsonl: {sum(r['kind'] == 'claim' for r in added)} claims, {sum(r['kind'] == 'idiom-np' for r in added)} idioms added, {len(out)} rows")


if __name__ == "__main__":
    main()
