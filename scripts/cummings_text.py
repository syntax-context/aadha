#!/usr/bin/env python3
"""Turn sources/cummings.epub (Complete Poems 1904-1962, every page a scanned image) into text.

30 October 2026, on Prayas's word: "parse this (after converting to a parseable format) for including in the
"desirable noise" context", then "use the existing cummings file only". The book is in copyright and stays in
sources/, which syntax/.gitignore keeps out of the public repository; nothing from it enters shipped data.

OCR is Tesseract 5 (psm 4), once per page, cached in sources/cummings/ocr.jsonl.gz with each word's position.
Layout is then rebuilt from those positions, because Cummings's spacing is part of the poem: a line's indent
from where its first word sits against the page's left margin, wide gaps inside a line as runs of spaces, and
a blank line where the vertical gap is larger than ordinary leading.

Writes sources/cummings/pages.jsonl (one page: index, printed page number if found, text) and
sources/cummings/cummings.txt (all pages, each headed "=== page <index> ===").
Run: python3 scripts/cummings_text.py   (from aadha-teetar-aadhi-bater/)
"""
import gzip, json, os, re, statistics, subprocess, tempfile, zipfile
from concurrent.futures import ThreadPoolExecutor

EPUB = 'sources/cummings.epub'
OUT = 'sources/cummings'
CACHE = f'{OUT}/ocr.jsonl.gz'
WORKERS = 4  # of 8 cores, leaving the machine its headroom


def ocr(path):
    r = subprocess.run(['tesseract', path, '-', '--psm', '4', '-c', 'preserve_interword_spaces=1', 'tsv'],
                       capture_output=True, text=True, env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
    words = []
    for row in r.stdout.splitlines()[1:]:
        f = row.split('\t')
        if len(f) == 12 and f[0] == '5' and f[11].strip():
            words.append([int(f[2]), int(f[3]), int(f[4]), int(f[6]), int(f[7]), int(f[8]), int(f[9]), f[11]])
    return words  # block, par, line, left, top, width, height, text


def layout(words):
    lines = {}
    for b, p, l, left, top, w, h, t in words:
        lines.setdefault((b, p, l), []).append((left, top, w, h, t))
    lines = sorted((sorted(ws) for ws in lines.values()), key=lambda ws: min(x[1] for x in ws))
    if not lines:
        return ''
    char_w = statistics.median(w / len(t) for ws in lines for _, _, w, _, t in ws if len(t) > 2) if any(
        len(t) > 2 for ws in lines for *_, t in ws) else 20
    gaps = [b[0] - (a[0] + a[2]) for ws in lines for a, b in zip(ws, ws[1:])]
    space = statistics.median(gaps) if gaps else char_w
    margin = min(ws[0][0] for ws in lines)
    leading = statistics.median(b[0][1] - a[0][1] for a, b in zip(lines, lines[1:])) if len(lines) > 1 else 0
    out, prev_top = [], None
    for ws in lines:
        top = min(x[1] for x in ws)
        if prev_top is not None and leading and top - prev_top > 1.5 * leading:
            out.append('')
        text = ws[0][4]
        for a, b in zip(ws, ws[1:]):
            text += ' ' * max(1, round((b[0] - (a[0] + a[2])) / space)) + b[4]
        out.append(' ' * round((ws[0][0] - margin) / char_w) + text)
        prev_top = top
    return '\n'.join(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    with zipfile.ZipFile(EPUB) as z:
        order = re.findall(r'<img src="([^"]+)"', z.read('index.html').decode())
        if not os.path.exists(CACHE):
            with tempfile.TemporaryDirectory() as tmp:
                z.extractall(tmp, order)
                with ThreadPoolExecutor(WORKERS) as pool:
                    pages = list(pool.map(lambda n: ocr(os.path.join(tmp, n)), order))
            with gzip.open(CACHE, 'wt') as f:
                for name, words in zip(order, pages):
                    f.write(json.dumps({'image': name, 'words': words}) + '\n')
    with gzip.open(CACHE, 'rt') as f:
        pages = [json.loads(l) for l in f]
    with open(f'{OUT}/pages.jsonl', 'w') as pj, open(f'{OUT}/cummings.txt', 'w') as txt:
        for i, p in enumerate(pages, 1):
            text = layout(p['words'])
            # a printed page number is a line of digits alone at the top or bottom
            ends = [l.strip() for l in text.splitlines() if l.strip()][:1] + [l.strip() for l in text.splitlines() if l.strip()][-1:]
            number = next((int(e) for e in ends if re.fullmatch(r'\d{1,4}', e)), None)
            pj.write(json.dumps({'index': i, 'image': p['image'], 'page': number, 'text': text}) + '\n')
            txt.write(f'=== page {i} ===\n{text}\n\n')
    print(f'{len(pages)} pages → {OUT}/pages.jsonl, {OUT}/cummings.txt')


if __name__ == '__main__':
    main()
