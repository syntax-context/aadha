#!/usr/bin/env python3
"""Claude Code's reading of every good-noise row (his word, 1 November 2026: "you (claude code) read everything 1 including what
stands. verify. dont assume"). The rows to read are grounding/read-1/chunk-NN.jsonl (id, text, src, kind), gathered from base i9,
the reflect adapter's rows and the Fig-QA metaphors; a Claude Code reader, Opus (his word, 1 November: "read with opus - not fable"), writes verdict-NN.jsonl beside each, one line per id
({"id", "keep", "why"}: why is noise, plain, idiom, nonsense or unsure). This script checks the verdicts cover every id exactly once
and merges them into grounding/read-1.jsonl ({"text", "keep", "why", "src", "kind", "reader", "date"}), which train.py's row loader
reads: a good-noise row not kept there, or not read at all, does not train. Nothing here reads a sentence; code only checks and merges.
usage: python read1.py   (prints what is missing, or writes grounding/read-1.jsonl)
"""
import datetime, glob, json, os, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(HERE, "grounding/read-1")
WHY = {"noise", "plain", "idiom", "nonsense", "unsure"}


def main():
    rows, out, missing = {}, [], []
    for chunk in sorted(glob.glob(os.path.join(D, "chunk-*.jsonl"))):
        n = re.search(r"chunk-(\d+)", chunk).group(1)
        items = {r["id"]: r for r in map(json.loads, open(chunk))}
        verdict = os.path.join(D, f"verdict-{n}.jsonl")
        got = {}
        if os.path.exists(verdict):
            for l in open(verdict):
                if l.strip():
                    v = json.loads(l)
                    if v["id"] in items and isinstance(v.get("keep"), bool) and v.get("why") in WHY and v["id"] not in got:
                        got[v["id"]] = v
        lost = sorted(set(items) - set(got))
        if lost:
            missing.append((n, len(items), len(got), lost[:8]))
        for i, v in got.items():
            out.append({"text": items[i]["text"], "keep": v["keep"], "why": v["why"], "src": items[i]["src"], "kind": items[i]["kind"],
                        "reader": "claude code, opus", "date": datetime.date.today().isoformat()})
    for n, total, done, lost in missing:
        print(f"chunk {n}: {done} of {total} read; missing ids start {lost}")
    if missing:
        print("not merged: every id must be read first")
        return
    with open(os.path.join(HERE, "grounding/read-1.jsonl"), "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in out)
    kept = sum(r["keep"] for r in out)
    print(f"grounding/read-1.jsonl: {len(out)} good-noise rows read, {kept} kept, {len(out) - kept} refused:",
          {w: sum(1 for r in out if not r["keep"] and r["why"] == w) for w in ("plain", "idiom", "nonsense", "unsure")},
          "; by source:", {s: (sum(1 for r in out if r['src'] == s and r['keep']), sum(1 for r in out if r['src'] == s)) for s in ("base", "reflect", "fig-qa")})


if __name__ == "__main__":
    main()
