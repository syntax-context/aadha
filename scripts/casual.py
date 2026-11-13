#!/usr/bin/env python3
"""Arm I4 (30 Oct 2026, 20:50). His word: "train", with the plan's six answers (next-version-plan.md): a misspelt word is one or
two letters from a real word, at most two in a sentence, and stays story; plainly told fantasy stays story; testers' new
sentences become training rows ("3 - training rows", "if novel"); verse is met by training on fragments; arm j deleted.
Arm I3's rows, plus:
  casual good noise  1  i3's claims, widened and layered rows typed casually, and new similes in first-person narration
  wry claims         1  plain-worded claims that mean more than they say
  misspelt story     2  corpus story with one or two words a letter off
  short story        2  corpus sentences of three to five words, which gen.py never took (it keeps 6 to 30)
  story fragments    2  corpus story cut at a comma, the first part kept with its comma
  tester rows        as keyed in grounding/tester-keys.jsonl, training part only, each twenty times
No content word of any hand set's, the probes' or tests/blindspots-i3.jsonl's good-noise lines is in the new tables, and no new
row is a sentence of any test set.
usage: python casual.py   (reads data-i3/ and the open corpus, writes data-i4/)
"""
import glob, importlib.util, json, os, random, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("poetic", os.path.join(HERE, "scripts/poetic.py")); poetic = importlib.util.module_from_spec(spec); spec.loader.exec_module(poetic)
spec = importlib.util.spec_from_file_location("vegan", poetic.VEGAN); vegan = importlib.util.module_from_spec(spec); spec.loader.exec_module(vegan)
CORPUS = os.path.join(HERE, "../../koher/ARCHIVE-SEPTEMBER-2026/mom-clean-base/data/pretrain")
SOURCES = ["gutenberg", "news", "wikimedia", "pressbooks", "libretexts", "hansard"]

SUBJ = ["the street noise", "her voice", "the horns below", "the long pause", "the scent of frying", "the radio upstairs", "the bustle outside",
        "the heat", "his excuse", "the phone screen", "the mirror in the stairwell", "the grime on the shelf"]
VERB = ["hung around", "went on", "stayed in the air", "drifted in", "spread over us", "hovered", "wandered from wall to wall"]
IMG = ["a visitor who had lost the directions", "a tune no one requested", "a coin rolling under a cabinet", "a letter with no stamp",
       "a cousin who never sits down", "a streamer after the party", "a question the lecturer pretends not to hear", "a receipt in a wet pocket",
       "a scooter that won't start in winter", "a tale looking for a listener"]
SIMILE = ["{s} {v} like {i}", "and {s} {v} like {i}", "{s} {v}, like {i}", "i noticed {s} {v} like {i}"]
THING = ["my scooter", "the staffroom kettle", "our dorm water cooler", "the elevator in our block", "my old cycle", "the photocopier",
         "the entry sheet at the gate", "my mother's handbag", "the wall clock", "our society noticeboard", "my umbrella", "the canteen menu"]
WRY = ["has heard more confessions than any priest", "has carried more worries than passengers", "has outlasted three principals and two renovations",
       "is the most reliable one in the household", "keeps better records than the treasury", "has been punctual more often than any of us",
       "has survived more quarrels than the sofa", "recalls every vow we quit mentioning", "is where good intentions go to idle",
       "has views about everyone and shares none", "is older than most of the rules it enforces", "has a longer recall than the staffroom"]
PLACE = ["colony", "dorm", "staffroom", "class", "block", "street"]
ACT = ["a cup of tea", "a forwarded message", "a lent charger", "a missed call", "an extra roti", "a shrug"]
MEANS = ["admit we were wrong", "apologise without apologising", "ask someone to stay", "show we were worried", "end a quarrel"]
TOOL = [("my helmet", "a rider"), ("my apron", "a cook"), ("my stethoscope", "a doctor"), ("my keys", "a resident"), ("my tiffin", "an employee"), ("my pass", "a commuter")]
PER = {"casual": (3000, 360, 360), "simile": (2000, 240, 240), "wry": (600, 80, 80), "misspelt": (5000, 600, 600), "short": (3000, 400, 400), "fragment": (3000, 400, 400)}
TESTS = sorted(glob.glob(os.path.join(HERE, "tests/**/*.jsonl"), recursive=True))
COMMON = set("about around down go good through t that their with into from like every where when they this what who only keeps never after before same each have keep open someone without was were had become the her his our my in on of a an is it its by for and to at you all no one already else between s both behind back how knew everyone could not she we us old just has been be out up i me made first small any still end turned once so your than more most does did do there here as are can will would am if or but then them him he it's".split())


def words(lines):
    return {w.lower() for line in lines for w in re.findall(r"[A-Za-z]+", line)} - COMMON


def casual(s, rng):
    s = s.lower().rstrip(".!?")
    r = rng.random()
    return s + "," if r < 0.25 else rng.choice(["and ", "but ", "so "]) + s if r < 0.45 else s


def typo(s, rng):
    ws = s.split(); idx = [i for i, w in enumerate(ws) if len(w) >= 4 and w.isalpha()]
    if not idx: return None
    for i in rng.sample(idx, min(len(idx), rng.choice([1, 1, 2]))):
        w, j = ws[i], rng.randrange(1, len(ws[i]) - 1)
        ws[i] = rng.choice([w[:j] + w[j + 1] + w[j] + w[j + 2:], w[:j] + w[j + 1:], w[:j] + w[j] + w[j:]])
    return " ".join(ws)


def corpus_short(rng):
    out = {p: [] for p in ("train", "tune", "held")}
    for src in ("gutenberg", "news", "wikimedia"):   # Hansard's and the textbooks' short lines are mostly cut-offs ("Friend and his right hon.")
        with open(os.path.join(CORPUS, src + ".txt"), encoding="utf-8", errors="ignore") as f:
            text = f.read(40_000_000)
        for s in re.split(r"(?<=[.!?])\s+", text):
            s = s.strip(); w = s.split()
            if 3 <= len(w) <= 5 and s[0].isupper() and s[-1] in ".!?" and re.fullmatch(r"[A-Z][A-Za-z ,'-]*[a-z][.!?]", s) and not re.search(r"\b(hon|Mr|Mrs|Dr|St|No|vol|ch|pp)\.?$", s) and not vegan.ANIMAL.search(vegan.ALLOWED.sub("", s)):
                out[poetic_split(s)].append(s)
    return {p: sorted(set(v)) for p, v in out.items()}


def poetic_split(s):   # gen.py's split, so a sentence is in the same part in every arm
    import hashlib
    h = int(hashlib.sha256(s.encode()).hexdigest(), 16) % 100
    return "held" if h < 8 else "tune" if h < 16 else "train"


def main():
    tests = [json.loads(l) for f in TESTS for l in open(f) if l.strip()]
    test_text = {t["text"] for t in tests} | {t["text"].lower().rstrip(".!?") for t in tests}
    marked = [json.loads(l) for f in sorted(glob.glob(os.path.join(HERE, "tests/rekeyed/*.jsonl"))) + [os.path.join(HERE, "tests/probe-i.jsonl"), os.path.join(HERE, "tests/blindspots-i3.jsonl")] for l in open(f) if l.strip()]
    good = [t["text"] for t in marked if t["label"] == 1]   # the sets keyed under the present marks
    tables = SUBJ + VERB + IMG + SIMILE + THING + WRY + PLACE + ACT + MEANS + [x for t in TOOL for x in t] + ["In our {p}, {a} is how we {m}.", "Without {t} I am {r} only in name."]
    have = words([re.sub(r"\{\w+\}", "", t) for t in tables])
    shared = words(good) & (have | {w + "s" for w in have} | {w[:-1] for w in have if w.endswith("s")})
    assert not shared, f"words of the test sets' good-noise lines are in the tables: {sorted(shared)}"
    rng = random.Random(59)
    short = corpus_short(rng)
    tester = [json.loads(l) for l in open(os.path.join(HERE, "grounding/tester-keys.jsonl"))]
    os.makedirs(os.path.join(HERE, "data-i4"), exist_ok=True)
    for k, part in enumerate(("train", "tune", "held")):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-i3/{part}.jsonl"))]
        made = {r["text"] for r in rows} | test_text
        added = []
        def add(text, label, kind, n=1):
            if text and text not in made and not vegan.ANIMAL.search(vegan.ALLOWED.sub("", text)):
                made.add(text); added.extend({"label": label, "kind": kind, "source": "casual.py", "text": text} for _ in range(n)); return True
            return False
        def fill(kind, label, maker):
            got, tries = 0, 0
            while got < PER[kind][k] and tries < 200000:
                tries += 1; got += add(maker(), label, kind)
        pool = [r["text"] for r in rows if r["kind"] in ("claim", "widened", "layered")]
        story = [r["text"] for r in rows if r["kind"] == "meaning"]
        fill("casual", 1, lambda: casual(rng.choice(pool), rng))
        fill("simile", 1, lambda: rng.choice(SIMILE).format(s=rng.choice(SUBJ), v=rng.choice(VERB), i=rng.choice(IMG)))
        def wry():
            r = rng.random()
            if r < 0.6: s = f"{rng.choice(THING)} {rng.choice(WRY)}."
            elif r < 0.85: s = f"In our {rng.choice(PLACE)}, {rng.choice(ACT)} is how we {rng.choice(MEANS)}."
            else: t, ro = rng.choice(TOOL); s = f"Without {t} I am {ro} only in name."
            s = s[:1].upper() + s[1:]
            return poetic.typed(s, rng) if rng.random() < 0.5 else casual(s, rng)
        fill("wry", 1, wry)
        fill("misspelt", 2, lambda: (lambda s: poetic.typed(s, rng) if s else None)(typo(rng.choice(story), rng)))
        fill("short", 2, lambda: poetic.typed(rng.choice(short[part]), rng) if short[part] else None)
        def fragment():
            s = rng.choice(story); head = s.split(",")[0]
            return poetic.typed(head + ",", rng).rstrip(",") + "," if "," in s and len(head.split()) >= 3 else None
        fill("fragment", 2, fragment)
        if part == "train":
            for t in tester: add(t["text"], t["label"], "tester", 20)
        out = rows + added
        rng.shuffle(out)
        with open(os.path.join(HERE, f"data-i4/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in out)
        count = {}
        for r in added: count[r["kind"]] = count.get(r["kind"], 0) + 1
        print(f"data-i4/{part}.jsonl: {len(out)} rows; added by kind {count}; short pool {len(short[part])}")


if __name__ == "__main__":
    main()
