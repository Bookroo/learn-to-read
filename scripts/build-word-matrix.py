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

# Grapheme→phoneme correspondences in the order lessons teach them.
# (lesson, grapheme, phonemes, final_only) — a word is "readable" at the first
# lesson where some segmentation of its spelling into taught graphemes spells
# out one of its CMUdict pronunciations.
CORRESPONDENCES = [
    (1, "m", ("M",), False),
    (1, "t", ("T",), False),
    (1, "a", ("AE",), False),
    (2, "s", ("S",), False),
    (3, "p", ("P",), False),
    (4, "i", ("IH",), False),
    (5, "n", ("N",), False),
    (6, "d", ("D",), False),
    (7, "o", ("AA",), False),
    (7, "o", ("AO",), False),
    (8, "b", ("B",), False),
    (9, "g", ("G",), False),
    (11, "s", ("Z",), True),  # final S saying /z/
    (12, "e", ("EH",), False),
    (13, "h", ("HH",), False),
    (15, "l", ("L",), False),
    (16, "c", ("K",), False),
    (17, "u", ("AH",), False),
    (18, "r", ("R",), False),
    (21, "ch", ("CH",), False),
    (22, "y", ("Y",), False),
    (23, "z", ("Z",), False),
    (24, "k", ("K",), False),
    (24, "ck", ("K",), False),
    (25, "qu", ("K", "W"), False),
    (25, "qu", ("KW",), False),  # phonics-tool cmudict merges K W → KW
]

HEART_WORDS = {"i": 14, "a": 14, "the": 14}

UNREADABLE = 10_000


def load_cmudict(needed):
    """word → list of stress-stripped pronunciations, variants included."""
    path = os.path.join(ROOT, "..", "..", "phonics-tool", "cmudict-0.7b.txt")
    prons = {}
    with open(path, encoding="latin-1") as f:
        for line in f:
            if line.startswith(";;;"):
                continue
            head, _, tail = line.partition("  ")
            word = re.sub(r"\(\d+\)$", "", head).lower()
            if word not in needed:
                continue
            phones = tuple(re.sub(r"\d", "", p) for p in tail.split())
            prons.setdefault(word, []).append(phones)
    return prons


def readable_lesson(word, prons):
    """Earliest lesson whose taught correspondences can decode the word.

    DP over (spelling position, pronunciation position); cell value is the
    smallest possible max-lesson over the graphemes used so far.
    """
    best = HEART_WORDS.get(word, UNREADABLE)
    for pron in prons.get(word, []):
        dp = [[UNREADABLE] * (len(pron) + 1) for _ in range(len(word) + 1)]
        dp[0][0] = 0
        for i in range(len(word) + 1):
            for j in range(len(pron) + 1):
                if dp[i][j] == UNREADABLE:
                    continue
                for lesson, g, phones, final_only in CORRESPONDENCES:
                    i2, j2 = i + len(g), j + len(phones)
                    if final_only and i2 != len(word):
                        continue
                    if word[i:i2] == g and pron[j:j2] == phones:
                        dp[i2][j2] = min(dp[i2][j2], max(dp[i][j], lesson))
        best = min(best, dp[len(word)][len(pron)])
    return best if best < UNREADABLE else None


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
        # The parent reads the story; the child only finds the target words.
        targets = {norm(w) for w in slide.get("words", [])}
        for tok in tokenize(slide.get("story", "")):
            if tok in targets:
                yield tok
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

    prons = load_cmudict(all_words)
    readable = {w: readable_lesson(w, prons) for w in all_words}
    first_used = {
        w: min((n for n, c in lessons if c[w]), default=None) for w in all_words
    }

    csv_path = os.path.join(ROOT, "WORD_MATRIX.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["word", "cpb_rank", "dolch_prek", "readable", "first_used", "total"]
            + [f"lesson-{n}" for n, _ in lessons]
        )
        for word in rows:
            w.writerow(
                [
                    word,
                    ranks.get(word, ""),
                    "x" if word in DOLCH_PRE_K else "",
                    readable[word] or "",
                    first_used[word] or "",
                    practiced[word] or "",
                ]
                + [(c[word] or "") for _, c in lessons]
            )

    write_html(
        os.path.join(ROOT, "WORD_MATRIX.html"),
        rows, ranks, practiced, lessons, readable, first_used,
    )

    n_ranked_practiced = sum(1 for w in ranks if practiced[w])
    n_dolch_practiced = sum(1 for w in DOLCH_PRE_K if practiced[w])
    print(f"{len(lessons)} lessons, {len(rows)} words")
    print(f"top-500 practiced so far: {n_ranked_practiced}/500")
    print(f"Dolch pre-K practiced so far: {n_dolch_practiced}/40")
    print(f"wrote {csv_path}")
    print(f"wrote {csv_path.replace('.csv', '.html')}")


def write_html(path, rows, ranks, practiced, lessons, readable, first_used):
    def cell_style(count):
        if not count:
            return ""
        # 1 → lightest, 8+ → deepest
        a = min(count, 8) / 8
        return f"background:rgba(46,111,82,{0.12 + 0.55 * a});"

    body = []
    body.append(
        "<tr><th class='w'>word</th><th>rank</th><th>Dolch</th>"
        "<th>read-<br/>able</th><th>1st<br/>use</th><th>total</th>"
    )
    for n, _ in lessons:
        body.append(f"<th>{n}</th>")
    body.append("</tr>")
    for word in rows:
        total = practiced[word]
        rank = ranks.get(word, "")
        dolch = "&#10003;" if word in DOLCH_PRE_K else ""
        r, u = readable[word], first_used[word]
        heart = " class='heart'" if word in HEART_WORDS else ""
        early = " class='early'" if u and (not r or u < r) else ""
        cls = " class='zero'" if not total else ""
        body.append(
            f"<tr{cls}><td class='w'>{word}</td><td>{rank}</td>"
            f"<td class='d'>{dolch}</td><td{heart}>{r or ''}</td>"
            f"<td{early}>{u or ''}</td><td class='t'>{total or ''}</td>"
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
  td.heart {{ color: #cf3f7c; font-weight: 600; }}
  td.early {{ color: #c2410c; font-weight: 600; }}
  tr.zero td {{ color: #b6bdb8; }}
  tr.zero td.w {{ color: #b6bdb8; font-weight: 400; }}
</style>
</head>
<body>
<h1>Word Practice Matrix</h1>
<p class="sub">How many times each word is practiced in each lesson (slides only;
book text not yet counted). Rows ordered by CPB top-500 rank, then by practice
count for words outside the top 500. Grayed rows are not yet practiced.
<b>read&#8209;able</b> = first lesson the word is decodable from taught
grapheme&#8211;phoneme correspondences (pink = taught as a heart word);
<b>1st&nbsp;use</b> = first lesson the word appears in practice
(<span style="color:#c2410c;font-weight:600">orange</span> = used before it is
readable). Regenerate with <code>python3 scripts/build-word-matrix.py</code>.</p>
<table>{''.join(body)}</table>
</body>
</html>"""
    with open(path, "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
