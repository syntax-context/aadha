#!/usr/bin/env python3
"""Arm C (29 Oct 2026): arm B's rows unchanged, with abstract poetic nonsense added as grammar without sense (label 1, kind
"poetic"), made by code from sentence shapes and word lists, so the label is how the row was made. His words, after the animal kept
still on a piece whose noise was poetic: "noise does not mean gibberish, make it very abstract poetic nonsense", "it was supposed
to be 1 - dance". aadha had never seen the kind and read it as the nearest kind it had (lesson 13z54); a kind is taught by writing
it down as rows (13z15). The noise lines of grounding/test-texts.txt are keyed before training as tests/hand-v3.jsonl, and no word of
theirs is in the lists below, so they stay unseen; the generator and that set come from one session, so it is a signal (13z35).
Arm D (29 Oct 2026, 21:50, his word "improve it more"): the same, with a wider generator: SHAPES_D and WIDE add the constructions
soup C still read as story (a thing that dreams or hopes, "itself", "changed into", similes, possessives, present tense, -ing
subjects) and more words; the words of tests/hand-v4.jsonl, keyed before arm D trained, are kept out of the lists as well.
Arm E (29 Oct 2026, 23:10, his word "if piece 1 is wrong - fix it. dont give up"): arm D's generator, plus story on the border,
labelled meaning (2): everyday figures of speech that mean something (a room that is a sauna by noon, a scooter that coughs) and
plain errands, each filler paired so the sentence holds. Soup D read some real story as noise (13z56); this teaches the line
from the story side. tests/hand-v5.jsonl was keyed before arm E: its noise words stay out of the poetic lists, and the words that
carry its figures of speech stay out of the story shapes.
usage: python poetic.py c|d|e   (reads data-b/, writes data-<arm>/ and tests/hand-v3.jsonl; adds half as many poetic rows as each part has
grammar-without-sense rows; every added row through rai's vegan scan)
"""
import importlib.util, json, os, random, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VEGAN = os.path.join(HERE, "../../koher/tools-dev/koher-engine-core/rai/tests/test_vegan.py")

ABSTRACT = """memory longing grief hunger absence logic courage wonder mercy doubt habit fortune rumour reason
sorrow meaning nothing everything permission innocence velocity gravity rhythm sleep thirst laughter regret delay hope envy
ambition boredom shyness kindness tension balance origin future history instinct purpose fever stillness hesitation""".split()
THING = """lantern spoon teacup button bicycle umbrella kettle compass pillow envelope candle drum basket bell thread needle
bucket key coin kite matchbox curtain chimney anchor bridge tunnel lamp rope wheel spade bottle glove helmet ribbon parcel cupboard
balcony harbour railway pebble garden orchard mountain desert island""".split()
TIME = "dusk midnight August Sunday winter yesterday dawn autumn March Friday spring December".split()
COLOUR = "grey amber violet crimson silver scarlet golden indigo copper white turquoise maroon".split()
ADJ = """hollow folding patient sleepy brittle careless invisible tender reluctant crooked upturned nervous gentle restless
polite dizzy endless secret lopsided""".split()
VERB = """swallowed whispered painted carried stitched balanced untied sharpened planted polished measured hid rented
ironed buried wrapped invented sold""".split()
VERB_I = "wandered dozed trembled evaporated shivered blinked knelt wept giggled rusted fainted bloomed".split()
PREP = "inside beneath behind across through beyond under against between".split()
NUM = "two three four five six eleven twelve".split()

SHAPES = [
    "The {adj} {abstract} of {time} {verb} a {thing} full of {abstract2}.",
    "A {colour} {abstract} {verb_i} {prep} the {abstract2} of the {things}.",
    "{Abstract} {verb} {num} {adj} {things} {prep} the {abstract2} of {time}.",
    "The {things} {verb} their {abstract} until {time} {verb_i} {prep} a {adj} {thing}.",
    "{Num} {colour} {things} {verb} the {abstract} of a {adj} {time}.",
    "My {abstract} {verb} the {thing} and the {thing2} {verb_i} in {colour}.",
    "When the {abstract} {verb_i}, the {things} {verb} a {adj} {abstract2}.",
    "The {thing} {verb} its {abstract} {prep} a {colour} {thing2} of {time}.",
    "{Time} {verb} the {abstract} {prep} a {thing} that {verb_i} twice.",
    "Our {things} {verb_i} because the {abstract} {verb} a {colour} {thing}.",
]


WIDE = {
    "abstract": "curiosity justice comfort luck gossip fatigue nostalgia victory debt freedom dignity modesty jealousy loyalty".split(),
    "thing": "tiffin scooter stapler ruler notebook doormat mattress telephone ticket switch wardrobe platform hammer bench fountain signboard".split(),
    "verb_mind": "believed hoped wondered imagined worried prayed hesitated pretended".split(),
    "verb_pres": "swallows paints carries stitches measures hides rents irons buries wraps".split(),
    "shape": "square spiral oval cube pyramid cylinder zigzag".split(),
    "gerund": "sleeping swimming singing knocking sweeping reading climbing polishing".split(),
    "adv": "carefully loudly softly quickly thinly sweetly patiently upward".split(),
    "change": "sank into|changed into|ripened into|hardened into".split("|"),
}
# Words of the original lists that tests/hand-v4.jsonl also uses: left out of arm D, kept in arm C so it reproduces.
D_DROP = {"chimney", "cupboard", "evaporated", "rumour", "sharpened", "umbrella"}
# Words of the lists that tests/hand-v5.jsonl's noise lines also use: left out of arm E only.
E_DROP = {"copper", "doormat", "garden", "gravity", "grief", "harbour", "hunger", "ironed", "kettle", "patiently", "polite", "rented", "sleeping",
          "spoon", "tender", "ticket", "yesterday"}
SHAPES_D = [
    "The {abstract} of {gerund} {verb} itself {prep} a {adj} {thing}.",
    "The {thing} {verb_mind} in a {abstract} built from {things}.",
    "A {colour} {shape} {verb} {time} out of its own {abstract}.",
    "{Gerund} {change} a {colour} {thing} full of {abstract}.",
    "The {things} {verb_mind} that {abstract} was a {adj} {thing}.",
    "{Num} {things} {verb} {time} as though it were a {adj} {abstract}.",
    "My {thing} is a {colour} {abstract} with {num} {things}.",
    "The {thing} {verb_pres} its {abstract} to a {adj} {thing2}.",
    "In the {abstract} of {time}, a {thing} {verb_i} {adv}.",
    "The {thing}'s {abstract} {verb_i} {prep} the {things} of {abstract2}.",
    "{Abstract} is the {thing} that {verb} {time}.",
    "Nobody {verb} a {thing} out of {abstract} and {abstract2}.",
    "Every {shape} {verb_mind} {adv} about the {abstract} of a {thing}.",
    "The {time} {change} a {adj} {thing} and {verb_i} {prep} its {abstract}.",
]


# Story on the border, arm E only. Each shape draws one row of a table, so what is said holds together.
PEOPLE = ("My aunt|Our neighbour|The peon|My classmate|The accountant|Ravi|Fatima|Joseph|Gurpreet|Anjali|The driver|The clerk|My father|Our teacher|"
          "Meena|Arjun|Salma|Thomas|Harpreet|Kavya|My sister|Our landlord|The watchman|My cousin").split("|")
FIGURES = [
    ("By {clock} the {room} was {heat}.", {"clock": ["noon", "two o'clock", "lunchtime", "the afternoon"], "room": ["kitchen", "bus", "staff room", "computer lab", "waiting room", "train coach", "shop"], "heat": ["a sauna", "a pressure cooker", "a frying pan", "a steam bath"]}),
    ("{person}'s {words} hit me like {impact}.", {"words": ["reply", "message", "joke", "warning", "question"], "impact": ["a slap", "a brick", "a wave", "a punch"]}),
    ("The {place} was {crowd} of people before the {event}.", {"place": ["platform", "market", "bus stand", "stadium", "college gate"], "crowd": ["a sea", "a river", "a wall", "a flood"], "event": ["match", "holiday", "results", "sale"]}),
    ("After {period}, my {space} looks like {mess}.", {"period": ["the exams", "the trip", "the wedding", "the holidays"], "space": ["desk", "room", "wardrobe", "bag"], "mess": ["a jungle", "a battlefield", "a junkyard", "a storm passed through it"]}),
    ("{news} went round the {group} {speed}.", {"news": ["News of the result", "Word of the holiday", "The gossip about the new principal", "News of the bonus"], "group": ["office", "colony", "department", "class group"], "speed": ["within an hour", "by lunch", "overnight", "before tea"]}),
    ("{machine} {complains} {when}.", {"pair": [("The old fan", "groans"), ("My scooter", "coughs"), ("The printer", "sulks"), ("The laptop", "wheezes"), ("The tap", "sighs"), ("The office door", "complains")], "when": ["every morning", "when it starts", "in winter", "every Monday", "after the rain"]}),
    ("The {stretch} {went} during the {event}.", {"stretch": ["hours", "minutes", "afternoon", "week"], "went": ["dragged", "flew", "crept"], "event": ["board meeting", "viva", "long journey", "practical exam"]}),
    ("{person} has a heart of {material}.", {"material": ["gold", "stone"]}),
    ("The {due} loomed over {group} {period}.", {"due": ["deadline", "audit", "inspection", "interview"], "group": ["us", "the whole office", "the class", "the team"], "period": ["all month", "for days", "the whole week"]}),
    ("{person} is the backbone of {unit}.", {"unit": ["our office", "the family", "the team", "the department"]}),
]
ERRANDS = [
    ("{person} paid the electricity bill at the counter on {day}.", {}),
    ("{person} renewed the passport at the passport office in {month}.", {}),
    ("{person} collected the marksheet from the college office on {day}.", {}),
    ("{person} submitted the scholarship form before the last date.", {}),
    ("Each family fills {n} buckets from the tap every morning.", {"n": ["two", "three", "four"]}),
    ("The canteen closes at {hour} on {day}.", {"hour": ["five", "six", "seven"]}),
    ("{person} took the {transport} to {city} on {day}.", {"transport": ["bus", "train", "auto"], "city": ["Vadodara", "Surat", "Rajkot", "Pune", "Jaipur"]}),
    ("The {shop} gave {person_l} a receipt for the {item}.", {"shop": ["stationery shop", "chemist", "hardware shop"], "item": ["pens", "medicines", "screws", "file covers"]}),
    ("{person} waited {n} minutes for the lift.", {"n": ["ten", "fifteen", "twenty"]}),
    ("The meeting was moved to {day} because of the holiday.", {}),
]
DAY = "Monday Tuesday Wednesday Thursday Friday Saturday".split()
MONTH = "January March June September November".split()
# The words that carry the figures of speech in tests/hand-v5.jsonl, kept out of the shapes above.
V5_FIGURES = {"oven", "laugh", "fire", "swamp", "inbox", "ice", "cold", "mountain", "climbed", "woke", "sleep", "crawled", "smoke", "rumour"}


def border(rng):
    shape, table = rng.choice(rng.choice([FIGURES, ERRANDS]))
    w = {k: rng.choice(v) for k, v in table.items() if k != "pair"}
    if "pair" in table:
        w["machine"], w["complains"] = rng.choice(table["pair"])
    person = rng.choice(PEOPLE)
    w.update(person=person, person_l=person if person[0].isupper() and not person.startswith(("My", "Our", "The")) else person[0].lower() + person[1:],
             day=rng.choice(DAY), month=rng.choice(MONTH))
    return shape.format(**w)


BORDER = {"train": 1200, "tune": 150, "held": 150}
_border_rng = random.Random(31)


def border_rows(part, vegan, seen):
    out = []
    while len(out) < BORDER[part]:
        s = border(_border_rng)
        if s in seen or vegan.ANIMAL.search(vegan.ALLOWED.sub("", s)):
            continue
        seen.add(s)
        out.append({"label": 2, "kind": "border", "source": "poetic.py", "text": typed(s, _border_rng)})
    return out


def typed(s, rng):   # gen.py's: a third of rows typed as people type
    return s.lower().rstrip(".!?") if rng.random() < 1 / 3 else s


def plural(word, wide):   # arm C wrote a plain "s" (matchboxs, compasss); arm D writes English plurals
    return word + ("es" if wide and re.search(r"(s|x|ch|sh)$", word) else "s")


def poem(rng, wide=False, drop=frozenset()):
    pick = lambda xs, *not_: rng.choice([x for x in xs if x not in not_ and x not in drop])
    abstract, thing = ABSTRACT + (WIDE["abstract"] if wide else []), THING + (WIDE["thing"] if wide else [])
    a, t = pick(abstract), pick(thing)
    w = {"abstract": a, "abstract2": pick(abstract, a), "thing": t, "thing2": pick(thing, t), "things": plural(pick(thing), wide),
         "time": pick(TIME), "colour": pick(COLOUR), "adj": pick(ADJ), "verb": pick(VERB), "verb_i": pick(VERB_I), "prep": pick(PREP), "num": pick(NUM)}
    if wide:
        w.update({k: pick(v) for k, v in WIDE.items() if k not in ("abstract", "thing")})
    s = rng.choice(SHAPES + SHAPES_D if wide else SHAPES)
    s = re.sub(r"\{([A-Z])(\w+)\}", lambda m: w[m.group(1).lower() + m.group(2)].capitalize(), s)
    return re.sub(r"\b([Aa]) (?=[aeiou])", r"\1n ", s.format(**w))


def hand_v3():
    """The test texts as a hand set, keyed by how each line was written: noise lines 1, story lines 2."""
    noise, out = set(NOISE_LINES), []
    for line in open(os.path.join(HERE, "archive/old-test-texts/test-texts.txt")):   # moved from grounding/ on 30 Oct 2026, 17:35, his word: "remove all old tes text files"
        line = line.strip()
        if line and not re.match(r"^\d\. |^teetar|^Paste", line):
            out.append({"label": 1 if line in noise else 2, "kind": "poetic" if line in noise else "meaning", "text": line})
    assert sum(x["label"] == 1 for x in out) == len(NOISE_LINES), "a noise line is missing from the test texts"
    return out


def main(arm):
    wide, edge = arm in ("d", "e"), arm == "e"
    spec = importlib.util.spec_from_file_location("vegan", VEGAN); vegan = importlib.util.module_from_spec(spec); spec.loader.exec_module(vegan)
    hand = hand_v3()
    with open(os.path.join(HERE, "tests/hand-v3.jsonl"), "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in hand)
    v4 = [r["text"] for r in map(json.loads, open(os.path.join(HERE, "tests/hand-v4.jsonl"))) if r["label"] == 1]
    v5 = [r["text"] for r in map(json.loads, open(os.path.join(HERE, "tests/hand-v5.jsonl"))) if r["label"] == 1] if edge else []
    seen = {w.lower() for line in NOISE_LINES + (v4 if wide else []) + v5 for w in re.findall(r"[A-Za-z]+", line) if len(w) > 3} - {"that", "their", "with", "into", "from", "itself", "about"}
    drop = (D_DROP if wide else set()) | (E_DROP if edge else set())
    lists = {w.lower() for w in ABSTRACT + THING + TIME + COLOUR + ADJ + VERB + VERB_I + (sum(WIDE.values(), []) if wide else []) for w in w.split()} - drop
    lists |= {w.lower() for s in SHAPES + (SHAPES_D if wide else []) for w in re.findall(r"[a-z]+", re.sub(r"\{\w+\}", "", s))}
    lists |= {w + "s" for w in lists}
    assert not seen & lists, f"words from the test set's noise lines are in the lists: {sorted(seen & lists)}"
    print("tests/hand-v3.jsonl:", len(hand), "lines,", sum(x["label"] == 1 for x in hand), "poetic; no shared words")
    rng, made = random.Random(29), set()
    if edge:
        words = {w.lower() for shape, table in FIGURES + ERRANDS for w in re.findall(r"[A-Za-z]+", shape + json.dumps(table) + " ".join(PEOPLE))}
        assert not V5_FIGURES & words, f"words that carry hand-v5's figures of speech are in the story shapes: {sorted(V5_FIGURES & words)}"
        seen_story = set()
    os.makedirs(os.path.join(HERE, f"data-{arm}"), exist_ok=True)
    for part in ("train", "tune", "held"):
        rows = [json.loads(l) for l in open(os.path.join(HERE, f"data-b/{part}.jsonl"))]
        want, added = sum(r["label"] == 1 for r in rows) // 2, []
        while len(added) < want:
            s = poem(rng, wide, drop)
            if s in made or vegan.ANIMAL.search(vegan.ALLOWED.sub("", s)):
                continue
            made.add(s)
            added.append({"label": 1, "kind": "poetic", "source": "poetic.py", "text": typed(s, rng)})
        if edge:   # story on the border, from its own random stream so the poetic rows are drawn as in arm D
            story = border_rows(part, vegan, seen_story)
            added += story
        out = rows + added
        rng.shuffle(out)
        with open(os.path.join(HERE, f"data-{arm}/{part}.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in out)
        print(f"data-{arm}/{part}.jsonl: {len(rows)} rows of arm b, {sum(r['kind'] == 'poetic' for r in added)} poetic and {sum(r['kind'] == 'border' for r in added)} border story added")


NOISE_LINES = """The colour of Tuesday folded itself into a silence shaped like a vowel.
Every window remembers the hour that forgot its own weight.
A blue arithmetic slept inside the echo of the stairs.
Distance hummed through the pockets of an unwritten afternoon.
The number nine dissolved into a softer kind of north.
Mirrors argued gently with the grammar of the floor.
The light owed the corridor three unfinished doors.
Somewhere a question melted into the colour of waiting.
The almirah dreamt in a language made of corners.
Ink grew roots in the quiet between two clocks.
The ceiling fan translated noon into a slower blue.
Every receipt is a small moon carrying its own weather.
The stairs exhaled a syllable older than the door.
Paper rivers forgot which way the afternoon leaned.
A forgotten verb unbuttoned the horizon.
Green silences queued at the edge of a theorem.
Tomorrow leaked through the hinges of an empty vowel.
The wind kept its promises in a jar of maps.
A quiet hexagon borrowed the evening from its own reflection.
The sound of waiting turned slowly into a pale staircase.
Seven shadows rehearsed the alphabet of a closed drawer.
The morning spilled its numbers into a sleeve of glass.
An orange syllable drifted through the architecture of a yawn.
Half a thought married the corner of a sideways cloud.
The hours wore their ladders inside out.
A pocket of silence counted backwards into velvet.""".splitlines()

if __name__ == "__main__":
    import sys
    main(sys.argv[1])
