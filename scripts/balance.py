#!/usr/bin/env python3
"""How much the animal dances, from aadha's marks. Code, never the model.
  0 gibberish and 1 the good noise count alike as noise (Prayas, 29 Oct 2026, 15:38: "full noise"); 2 is story. The good noise is more than the
  everyday amount of abstraction, analogy or layered meaning, poetic nonsense, and grammar bent on purpose (his words, 30 Oct 2026).
  Three settings, each with a default proposed on 29 Oct 2026 and set by whoever runs it (his word, 29 Oct 2026: "make it configurable"):
    --half       the noise share at which the animal dances fully, default 0.15 (his word, 30 Oct 2026: "15% noise, resteaning"; 0.4 from 29 Oct)
    --reach      how far from HALF it still dances, fading to stillness at HALF +/- REACH, default 0.12 (his word, 4 Nov 2026, 15:17)
    --at-least   sentences a piece needs before it can be in balance at all, default 4
usage: python balance.py [--half 0.15] [--reach 0.12] [--at-least 4] 0 2 2 1 0 2      (the marks, one per sentence)
"""
import argparse


def sick(marks, at_least=4, undesirable_max=0.02, sick_below=0.05):
    """True when the animal looks sick (his words, 30 October 2026, 12:56: "below 5 desirable noise should make animal act sick"): less than sick_below of the good noise, in a piece not already still."""
    n = len(marks)
    return n >= at_least and sum(m == 1 for m in marks) / n < sick_below   # sick wins over the unwanted cap (his word, 12:59: "sick")


def dance(marks, half=0.15, reach=0.12, at_least=4, undesirable_max=0.02):
    """0 (still) to 1 (dancing fully). Two checks (his words, 30 October 2026, 12:45: "the 15 is the desirable noise. undesirable noise can be upto 2% only"): the share of desirable noise (1) sets the
    dance; more than undesirable_max of undesirable noise (0) keeps it still."""
    if len(marks) < at_least or sum(m == 0 for m in marks) / len(marks) > undesirable_max:
        return 0.0
    good = sum(m == 1 for m in marks) / len(marks)
    return round(max(0.0, 1 - abs(good - half) / reach), 2)   # an edge (1 in 10 at 0.15 +/- 0.05) is 0, not 2e-16


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--half", type=float, default=0.15)
    ap.add_argument("--reach", type=float, default=0.12)
    ap.add_argument("--at-least", type=int, default=4)
    ap.add_argument("--undesirable-max", type=float, default=0.02)
    ap.add_argument("--sick-below", type=float, default=0.05)
    ap.add_argument("marks", type=int, nargs="+")
    a = ap.parse_args()
    m = a.marks
    print(f"desirable {sum(x == 1 for x in m) / len(m):.2f}, undesirable {sum(x == 0 for x in m) / len(m):.2f}, dance {dance(m, a.half, a.reach, a.at_least, a.undesirable_max):.2f}{", looks sick" if sick(m, a.at_least, a.undesirable_max, a.sick_below) else ""}")
