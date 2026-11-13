#!/usr/bin/env python3
"""Arm H (30 Oct 2026). His words: "more than the normal amount of abstraction, layered meaning, analogy etc are considered noise but
are the desirable kind of noise ... make sure model does this". So label 1 widens from grammar without sense to the desirable noise:
poetic nonsense, and writing with more than the everyday amount of abstraction, analogy or layered meaning. Plain writing and the
everyday idiom (a heart of gold, the office was an oven) stay story (2); gibberish stays the undesirable noise (0). Where the
everyday amount ends is his to judge; the line drawn here, and in tests/hand-v9.jsonl, is a proposal: a conventional idiom is story;
a fresh image, an extended analogy, or an abstraction made to act is desirable noise.
Arm G's rows, plus analogy, metaphor and abstraction sentences made by code from themed tables (label 1, kind "layered"), some within
one theme and some across two, which only makes the image stranger and keeps the label. Two lines of the test texts that arm G
taught as story are desirable noise by this rule and are relabelled. No content word of hand-v9's noise lines is in the tables.
usage: python layered.py   (reads data-g/, writes data-h/)
"""
import importlib.util, json, os, random, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("poetic", os.path.join(HERE, "scripts/poetic.py")); poetic = importlib.util.module_from_spec(spec); spec.loader.exec_module(poetic)
spec = importlib.util.spec_from_file_location("vegan", poetic.VEGAN); vegan = importlib.util.module_from_spec(spec); spec.loader.exec_module(vegan)

# Each theme: things people do (said as an -ing phrase) and images they can be likened to.
THEMES = {
    "office": (["filling in a reimbursement claim", "standing at the accounts counter", "getting a signature from the registrar", "renewing a ration card", "chasing a refund"],
               ["a well that answers every bucket with its own voice", "a stairway that adds a step for every one you climb", "a river that only flows when nobody is watching",
                "a lock that keeps changing its own keyhole", "a postbox that sorts letters by mood", "a game whose rules are announced after it ends"]),
    "study": (["revising before the finals", "writing a thesis", "practising how to draw hands", "reading a textbook in English", "preparing for a viva"],
              ["walking backwards up a hill of sand", "tying a raft together while already at sea", "trying to keep water in a sieve made of questions",
               "topping up a well with a cup", "tuning an instrument that keeps growing strings", "lighting lamps in a hall with no walls"]),
    "family": (["growing up in a joint family", "cooking with my nani", "listening to my father's stories", "visiting my village after years", "sharing a bicycle with my sister"],
               ["living inside a radio that plays every station at once", "reading a book whose pages are still being printed", "wearing a coat stitched from everyone's old sleeves",
                "a tree that keeps its leaves in someone else's pockets", "an orchestra where nobody owns the score", "a festival that never quite finishes"]),
    "travel": (["taking the local train at rush hour", "crossing the road at the crossroads", "riding a scooter through the old quarter", "sitting through a delayed flight", "looking for an address in a new town"],
               ["swimming in a crowd that has decided where you are going", "threading a needle on a swaying swing", "reading a novel copied out by a hundred hands",
                "dancing with partners who never introduce themselves", "a chess game where every piece is late", "a choir in which everyone sings a different hymn"]),
    "time": (["growing older", "recalling my first classroom", "longing for the monsoon", "looking at old photographs", "counting the days to a holiday"],
             ["a tide that only goes out", "a clock that keeps every hour it has struck", "a train that drops passengers without stopping",
              "a candle that lights the hall it is leaving", "a river that counts each stone it has passed", "a library that lends you only the books you have lost"]),
    "work": (["looking for a first job", "running a small shop", "working two shifts", "asking for a raise", "freelancing from home"],
             ["carrying a pot of water across a crowded fair", "planting seeds in a field that keeps shifting", "selling umbrellas to the sun",
              "knitting a sweater for a neighbour's winter", "a bamboo pole leaning against the sky", "a kite flown indoors with the fan on"]),
}
ABSTRACT = ["patience", "ambition", "loneliness", "courage", "envy", "kindness", "doubt", "loyalty", "curiosity", "regret", "pride", "faith", "habit", "forgiveness"]
ABSTRACT_IMAGES = ["a lamp carried into the day", "a coin that changes face when no one looks", "a visitor who rearranges the cushions", "an unpaid debt that keeps the roof up",
                   "a key cut for a lock that has moved", "a well that rises from below", "a letter addressed to its own sender", "a stairway that only goes down in the evening",
                   "a seed that carries the whole forest", "a mirror that shows the hall before you came in", "a debt the heart pays in small change", "a window that opens inwards"]
SHAPES = ["{Doing} is like {image}.", "{Doing} felt like {image}.", "For me, {doing} has always been {image}.", "{Doing} is, in the end, {image}."]
SHAPES_ABSTRACT = ["{Abstract} is {aimage}.", "{Abstract} is just {aimage}.", "Sometimes {abstract} is {aimage}."]
# Grammar bent on purpose, the way e e cummings bends it (his words, 30 Oct 2026: "so e e cummings kind of is considered the desirable
# kind of noise", "poetic nonsense is desirable noise"): made-up patterns in that manner, lower case, never his own lines.
BENT = {"who": ["she", "he", "they", "nobody", "someone", "everyone"], "pair": [("sang", "danced"), ("laughed", "wept"), ("came", "went"), ("stayed", "left"), ("spoke", "listened"), ("sold", "bought"), ("slept", "woke")],
        "adv": ["pretty", "rather", "quite", "very", "almost"], "q": ["how", "why", "when", "which"], "place": ["lane", "colony", "market", "village", "street", "town"],
        "dir": ["up", "down", "in", "out"], "adj": ["floating", "sleepy", "careful", "singing", "hushed"], "plural": ["bells", "kites", "windows", "leaves", "trains", "lamps"]}
SHAPES_BENT = ["{who} {v1} {poss} didn't {who} {v2} {poss} did", "{who} walked in a {adv} {q} {place}", "with {dir} so {adj} many {plural} {dir2}",
               "{who} {v1} {poss} {q} and {v2} {poss} {q2}", "({adv} {adj} {plural}) {who} {v1} not"]
POSS = {"she": "her", "he": "his", "they": "their", "nobody": "their", "someone": "their", "everyone": "their"}
PER_PART = {"train": 12000, "tune": 1500, "held": 1500}   # tripled 30 Oct, 13:05, when the re-keying left desirable noise at 7% of the rows
# Two lines of the test texts that arm G taught as story; by the rule above they are the desirable noise.
RELABEL = {"For days the sky held its breath over the city.", "My street smelled of wet earth and relief."}


def sentence(rng):
    r = rng.random()
    if r < 0.2:
        who = rng.choice(BENT["who"]); v1, v2 = rng.choice(BENT["pair"]); d1, d2 = rng.sample(BENT["dir"], 2); q1, q2 = rng.sample(BENT["q"], 2)
        return rng.choice(SHAPES_BENT).format(who=who, v1=v1, v2=v2, poss=POSS[who], adv=rng.choice(BENT["adv"]), q=q1, q2=q2, place=rng.choice(BENT["place"]),
                                               dir=d1, dir2=d2, adj=rng.choice(BENT["adj"]), plural=rng.choice(BENT["plural"]))
    if r < 0.4:
        w = {"abstract": rng.choice(ABSTRACT), "aimage": rng.choice(ABSTRACT_IMAGES)}
        s = rng.choice(SHAPES_ABSTRACT)
    else:
        t1 = rng.choice(list(THEMES)); t2 = t1 if rng.random() < 0.6 else rng.choice(list(THEMES))
        w = {"doing": rng.choice(THEMES[t1][0]), "image": rng.choice(THEMES[t2][1])}
        s = rng.choice(SHAPES)
    s = re.sub(r"\{([A-Z])(\w+)\}", lambda m: w[m.group(1).lower() + m.group(2)][:1].upper() + w[m.group(1).lower() + m.group(2)][1:], s)
    return s.format(**w)


def main():
    v9 = [r["text"] for r in map(json.loads, open(os.path.join(HERE, "tests/hand-v9.jsonl"))) if r["label"] == 1]
    seen = {w.lower() for line in v9 for w in re.findall(r"[A-Za-z]+", line) if len(w) > 3} - {"that", "their", "with", "into", "from", "itself", "about", "like", "every", "where", "when", "they", "this", "what", "who", "only", "keeps", "never", "already", "after", "before", "same", "made", "each", "else", "everyone", "first", "have", "keep", "open", "small", "someone", "without", "different"}
    tables = " ".join(sum((a + b for a, b in THEMES.values()), []) + ABSTRACT + ABSTRACT_IMAGES + SHAPES + SHAPES_ABSTRACT + SHAPES_BENT + [w for v in BENT.values() for x in v for w in (x if isinstance(x, tuple) else (x,))])
    words = {w.lower() for w in re.findall(r"[A-Za-z]+", re.sub(r"\{\w+\}", "", tables))}
    shared = seen & (words | {w + "s" for w in words} | {w[:-1] for w in words if w.endswith("s")})
    assert not shared, f"words of hand-v9's noise lines are in the tables: {sorted(shared)}"
    rng, made = random.Random(43), set()
    os.makedirs(os.path.join(HERE, "data-h"), exist_ok=True)
    for part in ("train", "tune", "held"):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-g/{part}.jsonl"))]
        relabelled = 0
        for r in rows:
            if r["kind"] == "test-text" and r["text"].rstrip(".").lower() in {x.rstrip(".").lower() for x in RELABEL}:
                r["label"] = 1; relabelled += 1
        made |= {r["text"] for r in rows}
        added, tries = [], 0
        while len(added) < PER_PART[part] and tries < 2000000:
            tries += 1
            s = sentence(rng)
            if s in made or vegan.ANIMAL.search(vegan.ALLOWED.sub("", s)):
                continue
            made.add(s)
            added.append({"label": 1, "kind": "layered", "source": "layered.py", "text": poetic.typed(s, rng)})
        out = rows + added
        rng.shuffle(out)
        with open(os.path.join(HERE, f"data-h/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in out)
        print(f"data-h/{part}.jsonl: {len(rows)} rows of arm g ({relabelled} test-text rows relabelled), {len(added)} layered added")


if __name__ == "__main__":
    main()
