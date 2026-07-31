#!/usr/bin/env python3
"""Build the word-practice matrix for Learn to Read lessons.

Counts how many times each word is practiced in each drafted lesson JSON
(rows = words, columns = lesson files) and joins the curriculum availability
engine: for every word, the curriculum lesson at which it first becomes
readable (data/curriculum.json via scripts/availability.py). Practice that
happens before a word is readable is flagged.

Lesson files map to curriculum lessons through data/lesson-map.json (file
number -> slug), so reordering the curriculum never silently misaligns the
matrix. Book text is not counted yet — ebook text lives in the CMS.

Usage:  python3 scripts/build-word-matrix.py
Reads:  lessons/lesson-*.json, data/curriculum.json, data/lesson-map.json,
        data/cpb-top-500.csv
Writes: WORD_MATRIX.csv, WORD_MATRIX.html
"""

import csv
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from availability import load as load_curriculum  # noqa: E402
from practice_counts import load_lesson_files  # noqa: E402


def main():
    cur = load_curriculum()
    dolch = set(json.load(open(
        os.path.join(ROOT, "data", "curriculum.json")))["dolch_pre_k"])
    ranks = {}
    with open(os.path.join(ROOT, "data", "cpb-top-500.csv")) as f:
        for row in csv.DictReader(f):
            w = row["word"].lower()
            if len(w) == 1 and w not in ("a", "i"):
                continue  # corpus noise: bare letters aren't words
            ranks[w] = int(row["rank"])

    # lesson file numbers match curriculum lesson numbers 1:1
    lessons = [(number, number, counts, read_counts)
               for number, counts, read_counts, _ in load_lesson_files(ROOT)]

    practiced = Counter()
    for _, _, counts, _ in lessons:
        practiced.update(counts)

    all_words = set(ranks) | dolch | set(practiced)
    rows = sorted(
        all_words,
        key=lambda w: (ranks.get(w, 10_000), -practiced[w], w),
    )
    avail = {w: cur.first_available(w)[0] for w in all_words}
    heart_all = {w.lower() for l in cur.lessons for w in l["heart"]}
    first_used = {
        w: min((cn for _, cn, c, _ in lessons if c[w]), default=None)
        for w in all_words
    }
    first_read = {
        w: min((cn for _, cn, _, rc in lessons if rc[w]), default=None)
        for w in all_words
    }

    csv_path = os.path.join(ROOT, "WORD_MATRIX.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["word", "cpb_rank", "dolch_prek", "available", "first_used", "total"]
            + [f"lesson-{n}" for n, _, _, _ in lessons]
        )
        for word in rows:
            w.writerow(
                [
                    word,
                    ranks.get(word, ""),
                    "x" if word in dolch else "",
                    avail[word] or "",
                    first_used[word] or "",
                    practiced[word] or "",
                ]
                + [(c[word] or "") for _, _, c, _ in lessons]
            )

    write_html(os.path.join(ROOT, "WORD_MATRIX.html"), rows, ranks, practiced,
               lessons, avail, first_used, first_read, heart_all, dolch)

    early = [w for w in all_words
             if first_read[w] and (avail[w] is None or first_read[w] < avail[w])]
    print(f"{len(lessons)} lessons, {len(rows)} words")
    print(f"top-500 practiced so far: {sum(1 for w in ranks if practiced[w])}/500")
    print(f"Dolch pre-K practiced so far: {sum(1 for w in dolch if practiced[w])}/40")
    print(f"READ before available: {len(early)}"
          + (f" — {', '.join(sorted(early))}" if early else ""))
    print(f"wrote {csv_path}")
    print(f"wrote {csv_path.replace('.csv', '.html')}")


def write_html(path, rows, ranks, practiced, lessons, avail, first_used,
               first_read, heart_all, dolch):
    def cell_style(count):
        if not count:
            return ""
        a = min(count, 8) / 8  # 1 → lightest, 8+ → deepest
        return f"background:rgba(46,111,82,{0.12 + 0.55 * a});"

    body = []
    body.append(
        "<tr><th class='w'>word</th><th>rank</th><th>Dolch</th>"
        "<th>avail</th><th>1st<br/>use</th><th>total</th>"
    )
    for n, cn, _, _ in lessons:
        note = f" title='curriculum lesson {cn}'" if cn != n else ""
        body.append(f"<th{note}>{n}</th>")
    body.append("</tr>")
    for word in rows:
        total = practiced[word]
        rank = ranks.get(word, "")
        d = "&#10003;" if word in dolch else ""
        a, u, r = avail[word], first_used[word], first_read[word]
        heart = " class='heart'" if word in heart_all else ""
        early = " class='early'" if r and (a is None or r < a) else ""
        cls = " class='zero'" if not total else ""
        body.append(
            f"<tr{cls}><td class='w'>{word}</td><td>{rank}</td>"
            f"<td class='d'>{d}</td><td{heart}>{a or ''}</td>"
            f"<td{early}>{u or ''}</td><td class='t'>{total or ''}</td>"
        )
        for _, _, counts, _ in lessons:
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
<p class="sub">How many times each word is practiced in each drafted lesson
(slides only; book text not yet counted). Rows ordered by CPB top-500 rank,
then by practice count for words outside the top 500. Grayed rows are not yet
practiced. <b>avail</b> = curriculum lesson at which the word first becomes
readable (pink = via heart word); <b>1st&nbsp;use</b> = first curriculum
lesson with practice (<span style="color:#c2410c;font-weight:600">orange</span>
= the child <i>reads</i> it before it is readable — listening-only exercises
don't count). Columns are lesson-file numbers; hover shows the
curriculum lesson where they differ. Regenerate with
<code>python3 scripts/build-word-matrix.py</code>.</p>
<table>{''.join(body)}</table>
</body>
</html>"""
    with open(path, "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
