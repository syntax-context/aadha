#!/usr/bin/env python3
"""His keys, the labels every training and test row rests on (1 November 2026, his words, 08:45: "I am liking the keying process -
all training jobs henceforth shou be based on my keying - my codified intelligence - not yours or any other ai's").

A sheet is blind: numbered lines with no model's mark showing. He writes 2 story, 1 the good noise, 3 common coin or 0 unwanted
noise after each, and under it the words of the sentence that are each of the three components he defines first in a components
file (2 November 2026, his words, 14:12: "all further keying will be with component defination - I will define"). Read back, the keys go into grounding/keys.jsonl, one line per keyed sentence ({"text", "key", "sheet", "date"},
the latest key for a sentence wins), which train.py's row loader applies to every row it reads, training and test alike, his key
overriding whatever the row carried and the row's earlier label kept beside it as "key_before". What a model marked is kept apart
in the sheet's check file, so his keys and the model's reading can be laid side by side afterwards and never mixed before.

usage:
  python keys.py --sheet <stem> <components.md> <rows.jsonl> [...]  shuffle the rows, write grounding/<stem>-keys.txt (blind, with lines
                                                                   1:, 2: and 3: under each key for the words that are each component,
                                                                   " ... " between two pieces of one part) and grounding/<stem>-check.jsonl
                                                                   (the rows as given, "his_key" empty); refused unless his components
                                                                   file names all three components
                                                                   A components file carrying the line "template: fixed" makes a sheet with no key to write:
                                                                   he marks the parts and answers its questions, and derive() works out the key
  python keys.py --read <stem>                                     read grounding/<stem>-keys.txt back into the check file and keys.jsonl
  python keys.py --read <keys.txt> <check.jsonl> <sheet name>      the same for a sheet made before this script
"""
import datetime, json, os, random, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(HERE, "grounding")
KEYS = os.path.join(G, "keys.jsonl")
WORDS = {2: "story", 1: "the good noise", 3: "common coin", 0: "unwanted noise"}


def keyed():
    """{text: his key}, the latest key for each sentence."""
    if not os.path.exists(KEYS):
        return {}
    return {r["text"]: r["key"] for r in map(json.loads, open(KEYS))}


READ1 = os.path.join(G, "read-1.jsonl")
COMPONENTS = os.path.join(G, "read-1", "components.jsonl")
REDEFINE = os.path.join(G, "read-1", "redefine.jsonl")


def read1():
    """{text: kept}: every sentence labelled the good noise that Claude Code has read against the page's definitions (his word, 1 November
    2026: "you (claude code) read everything 1 including what stands. verify. dont assume"). A good-noise row not in this file, or not
    kept, is not trained on (train.py's row loader drops it). Made by scripts/read1.py from grounding/read-1/."""
    if not os.path.exists(READ1):
        return {}
    kept = {r["text"]: r["keep"] for r in map(json.loads, open(READ1))}
    # template lines read again under his components rule (2 November 2026, his word: "apply rule to all template lines") replace the first
    # reading: kept only where read as the good noise; a line read as anything else is dropped, never given that mark
    if os.path.exists(COMPONENTS):
        kept.update({r["text"]: r["code"] == "N" for r in map(json.loads, open(COMPONENTS))})
    kept.update({t: True for t, c in redefined().items() if c == "N"})   # read as the good noise under the definitions of 2 November
    return kept


def read_components():
    """{text: code}: template lines as read under his components rule (2 November 2026). 3 November, his word "either fix aadha with
    measurement or with training": a line read as verbiage (X) trains as unwanted noise and one read as stock (I) as common coin, where
    they were dropped before, because the model then met that shape only in rows of other kinds."""
    if not os.path.exists(COMPONENTS):
        return {}
    return {r["text"]: r["code"] for r in map(json.loads, open(COMPONENTS))}


def read_own():
    """({text: label}, {held-out text}) from own/labels.jsonl: Claude's own reading, on his word of 3 November 2026 ("discard my keys and components - make your own read"), for arms named o..., in place of his keys."""
    rows = [json.loads(l) for l in open(os.path.join(os.path.dirname(G), "own", "labels.jsonl"))]
    return {r["text"]: r["label"] for r in rows}, {r["text"] for r in rows if r["held"]}


def redefined():
    """{text: code}: every line decided under the old definition (story rows of i11, good-noise rows refused as plain), read again by Opus
    under his definitions of 2 November 2026 (15:46: "new framing is precise"; 15:51: "make corrections to all training as per old
    definition"), in which a reflective or philosophical claim is the good noise. Made by grounding/read-briefs/redefine.py."""
    if not os.path.exists(REDEFINE):
        return {}
    return {r["text"]: r["code"] for r in map(json.loads, open(REDEFINE))}


def derive(a):
    """The key that follows from a line marked on the fixed template (grounding/components-template.md), or None when it gives no key."""
    if a.get("reads") == "n":
        return 0
    if not a.get("1"):
        return None
    if a.get("3"):
        if a.get("worn") == "y":
            return {"y": 3, "n": 2}.get(a.get("leans"))
        if a.get("worn") not in ("n", "y+") or a.get("carries") in (None, "", "?"):
            return None
        return 0 if a["carries"] == "nothing" else 1
    usual = a.get("usual", "")
    return {"": 2, "?": None, "saying": 3}.get(usual, 1)


def sheet(stem, components, files):
    text = open(components).read()
    names = re.findall(r"^name:[ \t]*(.*?)[ \t]*$", text, re.M)
    if len(names) != 3 or not all(names):
        sys.exit(f"no sheet: {components} must name three components, and the names are his to write")
    fixed = re.search(r"^template: fixed$", text, re.M)
    rows = [json.loads(l) for f in files for l in open(f) if l.strip()]
    random.Random(stem).shuffle(rows)
    with open(os.path.join(G, f"{stem}-keys.txt"), "w") as f:
        if fixed:
            f.write(f"{stem}: {len(rows)} lines. Write no key: mark the parts and answer the questions in {os.path.relpath(components, G)}, and code works out the key. "
                    f"After 1:, 2: and 3: copy the words of the sentence exactly as they stand, \" ... \" between two pieces, or leave it empty. "
                    f"The line numbers match {stem}-check.jsonl, which holds what a model read; keep that file closed while keying.\n\n")
        else:
            f.write(f"{stem}: {len(rows)} lines. After each number write 2 for story, 1 for the good noise, 3 for common coin or 0 for unwanted noise. "
                    f"After 1:, 2: and 3: copy the words of the sentence that are that component of {os.path.relpath(components, G)} "
                    f"(1 {names[0]}; 2 {names[1]}; 3 {names[2]}), exactly as they stand, \" ... \" between two pieces, or write none. "
                    f"The line numbers match {stem}-check.jsonl, which holds what a model read; keep that file closed while keying.\n\n")
        for k, r in enumerate(rows, 1):
            f.write(f"{k}. {r['text']}\nreads: \n1: \n2: \n3: \nworn: \nleans: \ncarries: \nusual: \n\n" if fixed else f"{k}. {r['text']}\nkey: \n1: \n2: \n3: \n\n")
    with open(os.path.join(G, f"{stem}-check.jsonl"), "w") as f:
        f.writelines(json.dumps({**r, "his_key": None}) + "\n" for r in rows)
    print(f"grounding/{stem}-keys.txt: {len(rows)} lines for his keys")


def read(txt, check, name):
    got, parts, wrong = {}, {}, []   # one block per line of the sheet, so a blank key stays blank and never takes the next line's key
    for block in re.split(r"\n[ \t]*\n", open(txt).read()):
        m = re.match(r"\s*(\d+)\. (.*?)\n(?:key:[ \t]*(\d?)[ \t]*(?:\n|$)|(?=reads:))", block, re.S)
        if not m or (m.group(3) is not None and not m.group(3)):
            continue
        n, said = int(m.group(1)), dict(re.findall(r"^(1|2|3|reads|worn|leans|carries|usual):[ \t]*(.*?)[ \t]*$", block[m.end():], re.M))
        bad = [c for c, w in said.items() if c in "123" and w and w != "none" and any(p not in m.group(2) for p in w.split(" ... "))]   # " ... " joins pieces
        if bad:   # a part whose words are not in the sentence: the line is not read until it is put right
            wrong.append((n, bad))
            continue
        key = int(m.group(3)) if m.group(3) else derive(said)
        if key is None:   # the fixed template gave no key: the line stays blank and comes back to him
            continue
        got[n] = key
        if any(said.values()):
            parts[n] = said
    if wrong:
        print("not read, a part's words are not in the sentence (line, component):", wrong)
    rows = [json.loads(l) for l in open(check) if l.strip()]
    blank = [i for i in range(1, len(rows) + 1) if i not in got]
    today = datetime.date.today().isoformat()
    with open(KEYS, "a") as f:
        for i, r in enumerate(rows, 1):
            r["his_key"] = got.get(i)   # a line left blank carries no key, whatever an earlier reading put there
            if i in parts:
                r["his_parts"] = parts[i]
            if i in got:
                f.write(json.dumps({"text": r["text"], "key": got[i], "sheet": name, "date": today, **({"parts": parts[i]} if i in parts else {})}) + "\n")
    with open(check, "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    print(f"{len(got)} keys read from {os.path.relpath(txt, HERE)} into grounding/keys.jsonl" + (f"; {len(blank)} lines left blank: {blank}" if blank else ""),
          "; his keys:", {WORDS[k]: sum(1 for v in got.values() if v == k) for k in (2, 1, 3, 0) if k in got.values()})


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "--sheet":
        sheet(a[1], a[2], a[3:])
    elif a[0] == "--read" and len(a) == 2:
        read(os.path.join(G, f"{a[1]}-keys.txt"), os.path.join(G, f"{a[1]}-check.jsonl"), a[1])
    elif a[0] == "--read":
        read(a[1], a[2], a[3])
