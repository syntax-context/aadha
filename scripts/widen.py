#!/usr/bin/env python3
"""Arm I2 (30 Oct 2026, 14:25). His words: "discard mall cummings-style training data from "arm i" and make it work for a
"imaginative-writing, general writing tool" -- retrain "arm i" if needed". Arm I's rows with two changes:
  1. Every row layered.py made from SHAPES_BENT (grammar bent in the cummings manner) is taken out. They were not the fifth of
     the good noise that layered.py's odds suggest: its other shapes ran out of new sentences, so bent rows filled the rest,
     7,176 of the 12,000 good-noise rows in training and all 750 in tune.
  2. The good noise widens past "X is like Y". Measured before this arm, soup i read all 22 story lines of tests/hand-v12.jsonl
     (fiction, dialogue, plainly told impossible events, plain prose, idiom) as story and all 8 unwanted lines as unwanted, but
     caught 5 of 12 good-noise lines, missing metaphors said without "like": "Her silence was a locked drawer ...", "His promises
     were paper boats ...". So metaphors made by code from new tables (kind "widened", mark 1) are added: a feeling or a bond
     said to be, to have become, or to move like, a thing it is not.
No content word of any hand set's good-noise lines (hand-v9, v10, v12) is in the tables.
usage: python widen.py   (reads data-i/, writes data-i2/)
"""
import importlib.util, json, os, random, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("poetic", os.path.join(HERE, "scripts/poetic.py")); poetic = importlib.util.module_from_spec(spec); spec.loader.exec_module(poetic)
spec = importlib.util.spec_from_file_location("vegan", poetic.VEGAN); vegan = importlib.util.module_from_spec(spec); spec.loader.exec_module(vegan)

# layered.py's five bent shapes, as people may have typed them (lower case, no closing stop).
W = r"(she|he|they|nobody|someone|everyone)"
BENT = re.compile(rf"^{W} \w+ (her|his|their) didn't {W} \w+ (her|his|their) did$|^{W} walked in a \w+ \w+ \w+$|"
                  rf"^with \w+ so \w+ many \w+ \w+$|^{W} \w+ (her|his|their) \w+ and \w+ (her|his|their) \w+$|^\(\w+ \w+ \w+\) {W} \w+ not$", re.I)

SUBJECT = ["her patience", "his anger", "my fear", "our partnership", "their marriage", "her laughter", "his flattery", "my homesickness",
           "the principal's praise", "their rivalry", "her confidence", "his jealousy", "my shyness", "our hurry", "the family's pride",
           "her ambition", "his kindness", "my worry", "their quarrel", "the neighbours' gossip", "her stubbornness", "his boredom"]
PLURAL_SUBJECT = ["his excuses", "her compliments", "my plans", "their rules", "our holidays", "her apologies", "his opinions", "the old ghazals"]
IMAGE = ["an umbrella opened indoors", "a letter no one would answer", "a lamp left on in an empty godown", "a radio stuck between two stations",
         "a coin balanced on its edge", "a sketch rubbed out halfway", "a cousin who had stayed too long", "a ceiling fan turning in winter",
         "a pass for a train already gone", "a knot that tightens when pulled", "an alarm set for the wrong century",
         "a photograph left out in the sun", "a scaffold around a temple under repair", "a kettle that never quite boils",
         "a pen that writes in someone else's hand", "a garden fenced on all four sides", 
         "a window painted shut", "a thread pulled loose from a sari", "a receipt for something never bought",
         "a tune whistled through a keyhole", "a road that loses track of its destination", "a puddle pretending to be a lake",
         "a speech rehearsed for an empty hall", "a festival lantern after the festival", "a wall clock running on prayers"]
PLURAL_IMAGE = ["unposted letters", "chalk marks on a wet board", "footprints filling with water", "candles lit at noon",
                "keys to gates long bricked up", "coins dropped in an empty fountain", "kites tangled on a wire", "umbrellas left on a bus"]
PLACE = ["the market", "the campus", "the old quarter", "the bus depot", "the courtyard", "the staff quarters", "the railway colony"]
WHEN = ["after the harvest", "in the off season", "on a holiday", "before the monsoon", "during the power cut"]
SHAPES = ["{S} was {i}.", "{S} had become {i}.", "{S} sat between us like {i}.", "{S} drifted through the flat like {i}.",
          "In that decade {s} was {i}.", "{S} was, by then, {i}."]
SHAPES_PLURAL = ["{P} were {pi}.", "{P} had become {pi}.", "{P} piled up like {pi}."]
SHAPES_PLACE = ["{L} {w} was {i}.", "{L} {w} felt like {i}."]
PER_PART = {"train": 4200, "tune": 500, "held": 500}   # the tables make about 5,240 different sentences
HAND = ["tests/hand-v9.jsonl", "tests/hand-v10.jsonl", "tests/hand-v12.jsonl"]
COMMON = {"that", "their", "with", "into", "from", "like", "every", "where", "when", "they", "this", "what", "who", "only", "keeps",
          "never", "after", "before", "same", "each", "have", "keep", "open", "someone", "without", "was", "were", "had", "become",
          "the", "her", "his", "our", "my", "in", "on", "of", "a", "an", "is", "it", "its", "by", "for", "and", "to", "at", "you",
          "behind", "all", "no", "one", "already", "else", "between", "s", "both", "back", "how", "knew", "everyone", "could", "not", "she", "we", "us", "old"}


def cap(s):
    return s[:1].upper() + s[1:]


def sentence(rng):
    r = rng.random()
    if r < 0.6:
        s = rng.choice(SUBJECT)
        return rng.choice(SHAPES).format(S=cap(s), s=s, i=rng.choice(IMAGE))
    if r < 0.8:
        return rng.choice(SHAPES_PLURAL).format(P=cap(rng.choice(PLURAL_SUBJECT)), pi=rng.choice(PLURAL_IMAGE))
    return rng.choice(SHAPES_PLACE).format(L=cap(rng.choice(PLACE)), w=rng.choice(WHEN), i=rng.choice(IMAGE))


def main():
    good = [r["text"] for f in HAND for r in map(json.loads, open(os.path.join(HERE, f))) if r["kind"] == "layered"]
    seen = {w.lower() for line in good for w in re.findall(r"[A-Za-z]+", line)} - COMMON
    tables = " ".join(SUBJECT + PLURAL_SUBJECT + IMAGE + PLURAL_IMAGE + PLACE + WHEN + SHAPES + SHAPES_PLURAL + SHAPES_PLACE)
    words = {w.lower() for w in re.findall(r"[A-Za-z]+", re.sub(r"\{\w+\}", "", tables))}
    shared = seen & (words | {w + "s" for w in words} | {w[:-1] for w in words if w.endswith("s")})
    assert not shared, f"words of the hand sets' good-noise lines are in the tables: {sorted(shared)}"
    rng, made = random.Random(47), set()
    os.makedirs(os.path.join(HERE, "data-i2"), exist_ok=True)
    for part in ("train", "tune", "held"):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-i/{part}.jsonl"))]
        kept = [r for r in rows if not (r["kind"] == "layered" and BENT.match(r["text"]))]
        made |= {r["text"] for r in rows}
        added, tries = [], 0
        while len(added) < PER_PART[part] and tries < 2000000:
            tries += 1
            s = sentence(rng)
            if s in made or vegan.ANIMAL.search(vegan.ALLOWED.sub("", s)):
                continue
            made.add(s)
            added.append({"label": 1, "kind": "widened", "source": "widen.py", "text": poetic.typed(s, rng)})
        out = kept + added
        rng.shuffle(out)
        with open(os.path.join(HERE, f"data-i2/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in out)
        print(f"data-i2/{part}.jsonl: {len(rows) - len(kept)} bent rows out, {len(added)} widened added, {len(out)} rows")


if __name__ == "__main__":
    main()
