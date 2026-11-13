"""Mark sentences with aadha. Each sentence gets one mark:
0 unwanted noise · 1 the good noise · 2 story · 3 common coin

    pip install torch transformers peft
    python use.py "The bus was late again." "Every mistake leaves a fingerprint on the next one."
    python use.py --reflect "..."      the reflect reader, for an argued or reflective piece

The marks are the reader's first choice, with no threshold. What a mark means for a piece of writing is decided by
code, never by the model: in teetar aadhi bater the balance of marks across a piece is what the page shows.
"""
import sys

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MARKS = {0: "unwanted noise", 1: "the good noise", 2: "story", 3: "common coin"}
REPO = "prayasabhinav/aadha"


def load(reflect=False):
    tok = AutoTokenizer.from_pretrained(REPO)
    model = AutoModelForSequenceClassification.from_pretrained(REPO)
    if reflect:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, REPO, subfolder="reflect")
    return tok, model.eval()


def marks(sentences, reflect=False):
    tok, model = load(reflect)
    with torch.no_grad():
        logits = model(**tok(sentences, padding=True, truncation=True, max_length=96, return_tensors="pt")).logits
    return [int(i) for i in logits.argmax(-1)]


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--reflect"]
    for s, m in zip(args, marks(args, "--reflect" in sys.argv)):
        print(m, MARKS[m], "·", s)
