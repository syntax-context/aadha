"""Swapped-word twins of an adapter's own story sentences, unwanted noise (0), as i7's swapped rows are (gen.py, rekey.py).
31 October 2026: plain and figurative, trained with only fully shuffled twins, read swapped-word nonsense as story on held-b (-43
and -67 rows against the live soup): a new form of story needs its unwanted twin in the same form (lesson 13z62), and short, casual
story needs short, casual nonsense beside it (13z64). So each content word (noun, verb, adjective, adverb) is replaced by one of the
same fine tag from another sentence of the same source, the grammar, casing, spacing and slips standing, at least three changed and
two thirds of them (gen.py's strict rule); and a share is cut to 8 to 14 words, half typed in lower case without a stop.
Needs spaCy with en_core_web_sm ."""
import spacy

SWAP = {"NOUN", "VERB", "ADJ", "ADV"}
nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])


def swapped(texts, n, rng):
    """Up to n swapped twins, a third of them short (8 to 14 words, half in lower case without a stop)."""
    docs = list(nlp.pipe(texts, batch_size=256))
    pool = {}
    for d in docs:
        for t in d:
            if t.pos_ in SWAP:
                pool.setdefault(t.tag_, []).append(t.text)
    out = []
    for d in rng.sample(docs, len(docs)):
        if len(out) >= n:
            break
        words, changed, content = [], 0, 0
        for t in d:
            if t.pos_ in SWAP:
                content += 1
                w = rng.choice(pool[t.tag_])
                changed += w.lower() != t.text.lower()
                words.append((w.capitalize() if t.i == 0 else w.lower() if t.text.islower() else w) + t.whitespace_)
            else:
                words.append(t.text_with_ws)
        if changed >= 3 and changed >= 2 * content / 3:
            s = "".join(words).strip()
            w = s.rstrip(".!?").split()
            if len(out) % 3 == 2 and len(w) > 9:   # every third, short
                s = " ".join(w[:rng.randint(8, min(14, len(w) - 1))])
                s = s.lower() if rng.random() < 0.5 else s[:1].upper() + s[1:] + "."
            out.append(s)
    return out
