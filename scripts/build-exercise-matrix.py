#!/usr/bin/env python3
"""Build the exercise matrix: rows = drafted lessons, columns = exercises.

Cells count each lesson's practice items for an exercise: distinct words
where a slide names one (a word's multi-slide walkthrough counts once),
otherwise slides. Exercise names
follow the app's labeling (LearnToReadViewer): multi-set variants get the
kid-facing game name (Eagle Eyes, Letter Setter, Picture Quest); single-set
variants use the generic technique label. A red ring means curriculum.json
introduces the exercise (intro chip) at a different lesson than its actual
first use.

Usage:  python3 scripts/build-exercise-matrix.py
Reads:  lessons/lesson-*.json, data/curriculum.json
Writes: EXERCISE_MATRIX.html
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from availability import load as load_curriculum  # noqa: E402


def exercise_name(slide):
    """App-facing exercise label for a slide, or None for plumbing slides."""
    t = slide.get("type")
    multi = len(slide.get("sets", []) or []) > 1
    if t == "grapheme-recall":
        # the new-letter variant is the modern Introduce Letter
        return ("Introduce Letter" if slide.get("variant") == "new-letter"
                else "Letter Recall")
    named = {
        "grapheme-trace-air": "Letter Formation",
        "grapheme-trace-palm": "Letter Formation",
        "grapheme-hand-shape": "Hand Shapes",
        "find-grapheme": "Eagle Eyes" if multi else "Find the Letter",
        "identify-sound": "Identify Sound",
        "introduce-sound": "Sound Isolation",
        "sound-to-grapheme": "Letter Setter" if multi else "Sound to Letter",
        "lost-sounds": "Lost Sounds",
        "sound-pick-word-stack": "Elephant Ears",
        "sound-at-position": "Sound Train",
        "sound-train": "Sound Train",
        "phoneme-blending": "Sound Detective",
        "finger-word": "Finger Words",
        "word-to-picture": "Picture Quest" if multi else "Word to Picture",
        "picture-to-word": "Picture to Word",
        "word-chain": "Word Chains",
        "brain-words": "Brain Words",
        "story-words": "Story Words",
        "card-stack": "Card Stack",
        "reading-fluency": "Reading Fluency",
        "books": "Read a Book",
        "teach-tam": "Teach Tam",
    }
    return named.get(t)


def word_key(slide):
    """The word a slide practices, or None if it isn't a single-word slide.

    Finger Words walks one word across several slides (assign, stick, blend);
    those share a key so the lesson gets credit for the word, not the reps.
    """
    word = slide.get("word")
    return word.strip().upper() if isinstance(word, str) else None


def main():
    cur = load_curriculum()

    rows = []  # (file_n, cur_n, title, Counter-like dict)
    first_use = {}
    order = []
    import glob
    import re
    from collections import Counter
    for path in sorted(glob.glob(os.path.join(ROOT, "lessons", "lesson-*.json")),
                       key=lambda p: int(re.search(r"(\d+)", os.path.basename(p)).group(1))):
        n = int(re.search(r"(\d+)", os.path.basename(path)).group(1))
        # lesson file numbers match curriculum lesson numbers 1:1
        lesson = cur.lessons[n - 1] if n <= len(cur.lessons) else None
        cur_n = n
        title = lesson["title"] if lesson else "?"
        counts = Counter()
        seen = set()
        for i, slide in enumerate(json.load(open(path))):
            name = exercise_name(slide)
            if not name:
                continue
            # keyless slides fall back to their index, so each counts once
            key = (name, word_key(slide) or i)
            if key in seen:
                continue
            seen.add(key)
            counts[name] += 1
        for name in counts:
            if name not in first_use:
                first_use[name] = cur_n
                order.append(name)
        rows.append((n, cur_n, title, counts))

    # curriculum intro chips for cross-checking (exercises only)
    chip_intro = {}
    for l in cur.lessons:
        for i in l["intros"]:
            chip_intro.setdefault(i["name"], l["n"])

    mismatches = []
    for name, n in first_use.items():
        if name in chip_intro and chip_intro[name] != n:
            mismatches.append((name, chip_intro[name], n))

    body = ["<tr><th class='w'>lesson</th>"]
    for name in order:
        body.append(f"<th><span class='vh'>{name}</span></th>")
    body.append("</tr>")
    for n, cur_n, title, counts in rows:
        label = f"L{cur_n} · {title}" + (f" <i>(file {n})</i>" if n != cur_n else "")
        body.append(f"<tr><td class='w'>{label}</td>")
        for name in order:
            c = counts.get(name, 0)
            classes = []
            if c and first_use[name] == cur_n and any(m[0] == name for m in mismatches):
                classes.append("bad")
            a = min(c, 6) / 6 if c else 0
            style = f"background:rgba(46,111,82,{0.12 + 0.5 * a});" if c else ""
            cls = f" class='{' '.join(classes)}'" if classes else ""
            body.append(f"<td{cls} style='{style}'>{c or ''}</td>")
        body.append("</tr>")

    note = ""
    if mismatches:
        items = "; ".join(f"{n}: chip says L{c}, first used L{u}" for n, c, u in mismatches)
        note = f"<p class='warn'>⚠ curriculum chip mismatches — {items}</p>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Learn to Read — Exercise Matrix</title>
<style>
  body {{ font-family: ui-sans-serif, -apple-system, sans-serif; font-size: 13px;
         color: #212622; background: #faf9f5; margin: 24px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  p.sub {{ color: #59635c; margin: 0 0 16px; max-width: 760px; }}
  p.warn {{ color: #b3382c; font-weight: 600; }}
  table {{ border-collapse: collapse; background: #fff; }}
  th, td {{ border: 1px solid #e6e2d8; padding: 3px 8px; text-align: center;
            font-variant-numeric: tabular-nums; }}
  th {{ background: #fcfbf8; font-size: 11px; color: #8a938c;
        vertical-align: bottom; height: 110px; }}
  th .vh {{ writing-mode: vertical-rl; transform: rotate(180deg);
            white-space: nowrap; display: inline-block; }}
  td.w, th.w {{ text-align: left; font-weight: 600; white-space: nowrap;
                position: sticky; left: 0; background: #fff; }}
  td.w i {{ color: #8a938c; font-weight: 400; font-size: 11px; }}
  th.w {{ background: #fcfbf8; height: auto; }}
  td.bad {{ outline: 2px solid #cf3f3f; outline-offset: -2px; }}
</style>
</head>
<body>
<h1>Exercise Matrix</h1>
<p class="sub">How much of each exercise appears in each drafted lesson — distinct
words where a slide names one (a word's multi-slide walkthrough counts once),
otherwise slides. Columns ordered by first appearance; a red ring marks an exercise's debut
lesson when curriculum.json's intro chip disagrees. Multi-set slides use
the kid-facing game name (Eagle Eyes, Letter Setter, Picture Quest);
single-set slides use the generic label. Regenerate with
<code>python3 scripts/build-exercise-matrix.py</code>.</p>
{note}
<table>{''.join(body)}</table>
</body>
</html>"""
    out = os.path.join(ROOT, "EXERCISE_MATRIX.html")
    open(out, "w").write(html)
    print(f"{len(rows)} lessons × {len(order)} exercises -> {out}")
    if mismatches:
        print(f"chip mismatches: {mismatches}")


if __name__ == "__main__":
    main()
