#!/usr/bin/env python3
"""Build the word-practice matrix for Learn to Read lessons.

Counts how many times each word is practiced in each lesson (rows = words,
columns = lessons) and cross-references the CPB top-500 frequency ranks and
the Dolch pre-K list. Book text is not counted yet — ebook text lives in the
CMS, not in this repo.

Usage:  python3 scripts/build-word-matrix.py
Reads:  lessons/lesson-*.json, data/cpb-top-500.csv
Writes: WORD_MATRIX.csv, WORD_MATRIX.html
"""

import csv
import glob
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOLCH_PRE_K = {
    "a", "and", "away", "big", "blue", "can", "come", "down", "find", "for",
    "funny", "go", "help", "here", "i", "in", "is", "it", "jump", "little",
    "look", "make", "me", "my", "not", "one", "play", "red", "run", "said",
    "see", "the", "three", "to", "two", "up", "we", "where", "yellow", "you",
}

WORD_RE = re.compile(r"[a-z]+(?:['’][a-z]+)*")


def norm(word):
    """Lowercase and keep only letters/internal apostrophes."""
    m = WORD_RE.search(str(word).lower().replace("’", "'"))
    return m.group(0) if m else None


def tokenize(text):
    return WORD_RE.findall(str(text).lower().replace("’", "'"))


def words_in_slide(slide):
    """Yield each practiced-word occurrence in a slide.

    Counted: words the child reads, blends, or listens for.
    Not counted: distractor picture labels, parent script, book ids.
    """
    t = slide.get("type")
    if t in ("finger-word", "touch-slide", "picture-to-word"):
        yield norm(slide["word"])
    elif t == "word-to-picture":
        for s in slide.get("sets", []):
            yield norm(s["word"])
    elif t == "sound-pick-word-stack":
        for entry in slide.get("words", []):
            yield norm("".join(g for g, _ in entry))
    elif t in ("card-stack",):
        for w in slide.get("values", []):
            yield norm(w)
    elif t in ("brain-words", "word-chain"):
        for w in slide.get("words", []):
            yield norm(w)
    elif t == "sound-at-position":
        for w in slide.get("words", []):
            yield norm(w["word"])
    elif t == "story-words":
        yield from tokenize(slide.get("story", ""))
    elif t == "reading-fluency":
        yield from tokenize(slide.get("text", ""))


def main():
    ranks = {}
    with open(os.path.join(ROOT, "data", "cpb-top-500.csv")) as f:
        for row in csv.DictReader(f):
            ranks[row["word"].lower()] = int(row["rank"])

    lesson_files = sorted(
        glob.glob(os.path.join(ROOT, "lessons", "lesson-*.json")),
        key=lambda p: int(re.search(r"(\d+)", os.path.basename(p)).group(1)),
    )
    lessons = []  # (number, Counter)
    for path in lesson_files:
        number = int(re.search(r"(\d+)", os.path.basename(path)).group(1))
        counts = Counter()
        for slide in json.load(open(path)):
            for w in words_in_slide(slide):
                if w:
                    counts[w] += 1
        lessons.append((number, counts))

    practiced = Counter()
    for _, counts in lessons:
        practiced.update(counts)

    all_words = set(ranks) | DOLCH_PRE_K | set(practiced)
    # Ranked words by rank, then unranked by total practice desc, then alpha.
    rows = sorted(
        all_words,
        key=lambda w: (ranks.get(w, 10_000), -practiced[w], w),
    )

    csv_path = os.path.join(ROOT, "WORD_MATRIX.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["word", "cpb_rank", "dolch_prek", "total"]
            + [f"lesson-{n}" for n, _ in lessons]
        )
        for word in rows:
            w.writerow(
                [
                    word,
                    ranks.get(word, ""),
                    "x" if word in DOLCH_PRE_K else "",
                    practiced[word] or "",
                ]
                + [(c[word] or "") for _, c in lessons]
            )

    write_html(os.path.join(ROOT, "WORD_MATRIX.html"), rows, ranks, practiced, lessons)

    n_ranked_practiced = sum(1 for w in ranks if practiced[w])
    n_dolch_practiced = sum(1 for w in DOLCH_PRE_K if practiced[w])
    print(f"{len(lessons)} lessons, {len(rows)} words")
    print(f"top-500 practiced so far: {n_ranked_practiced}/500")
    print(f"Dolch pre-K practiced so far: {n_dolch_practiced}/40")
    print(f"wrote {csv_path}")
    print(f"wrote {csv_path.replace('.csv', '.html')}")


def write_html(path, rows, ranks, practiced, lessons):
    def cell_style(count):
        if not count:
            return ""
        # 1 → lightest, 8+ → deepest
        a = min(count, 8) / 8
        return f"background:rgba(46,111,82,{0.12 + 0.55 * a});"

    body = []
    body.append("<tr><th class='w'>word</th><th>rank</th><th>Dolch</th><th>total</th>")
    for n, _ in lessons:
        body.append(f"<th>{n}</th>")
    body.append("</tr>")
    for word in rows:
        total = practiced[word]
        rank = ranks.get(word, "")
        dolch = "&#10003;" if word in DOLCH_PRE_K else ""
        cls = " class='zero'" if not total else ""
        body.append(
            f"<tr{cls}><td class='w'>{word}</td><td>{rank}</td>"
            f"<td class='d'>{dolch}</td><td class='t'>{total or ''}</td>"
        )
        for _, counts in lessons:
            c = counts[word]
            body.append(f"<td style='{cell_style(c)}'>{c or ''}</td>")
        body.append("</tr>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Learn to Read — Word Practice Matrix</title>
<style>
  body {{ font-family: ui-sans-serif, -apple-system, sans-serif; font-size: 13px;
         color: #212622; background: #faf9f5; margin: 24px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  p.sub {{ color: #59635c; margin: 0 0 16px; max-width: 720px; }}
  table {{ border-collapse: collapse; background: #fff; }}
  th, td {{ border: 1px solid #e6e2d8; padding: 2px 7px; text-align: center;
            font-variant-numeric: tabular-nums; }}
  th {{ position: sticky; top: 0; background: #fcfbf8; font-size: 11px;
        color: #8a938c; z-index: 2; }}
  td.w, th.w {{ text-align: left; font-weight: 600; position: sticky; left: 0;
                background: #fff; z-index: 1; }}
  th.w {{ background: #fcfbf8; z-index: 3; }}
  td.d {{ color: #cf3f7c; }}
  td.t {{ font-weight: 600; }}
  tr.zero td {{ color: #b6bdb8; }}
  tr.zero td.w {{ color: #b6bdb8; font-weight: 400; }}
</style>
</head>
<body>
<h1>Word Practice Matrix</h1>
<p class="sub">How many times each word is practiced in each lesson (slides only;
book text not yet counted). Rows ordered by CPB top-500 rank, then by practice
count for words outside the top 500. Grayed rows are not yet practiced.
Regenerate with <code>python3 scripts/build-word-matrix.py</code>.</p>
<table>{''.join(body)}</table>
</body>
</html>"""
    with open(path, "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
