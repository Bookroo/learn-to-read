#!/usr/bin/env python3
"""Build the review queue: which known words need more practice?

Three lists, all limited to words a learner can actually decode (spelling
tiling AND CMUdict pronunciation must both clear — sound-wrong spelling
matches like "says"/"two"/"day" never qualify):

  1. Heart retention — heart words that haven't been re-read often enough
     after their teaching lesson (spaced retrieval).
  2. Backfill queue — top-500 words decodable for a while but never read
     in any lesson; the shopping list for review lessons and fluency
     sentences.
  3. One-shot words — top-500 words read in exactly one lesson and not
     seen since.

Plus a per-lesson load table so added review never overloads a lesson.
Early lessons are deliberately exempt: everything is new in Module 1 and
every word is slow, so the review budget ramps by module (see BUDGET).

Usage:  python3 scripts/build-review-queue.py
Reads:  data/curriculum.json, lessons/lesson-*.json, data/cpb-top-500.csv,
        ../../phonics-tool/cmudict-0.7b.txt
Writes: REVIEW_QUEUE.html
"""

import csv
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from availability import load, cmu_correspondences, cmu_readable  # noqa: E402
from practice_counts import load_lesson_files  # noqa: E402

# Review policy, per module. reps_cap = max total read-word reps a lesson
# should carry (overload guard); review_target = distinct previously-read
# words a lesson should ideally revisit (0 = module exempt from review
# pressure — Module 1 is all-new and slow by design).
BUDGET = {
    1: {"reps_cap": 12, "review_target": 0},
    2: {"reps_cap": 36, "review_target": 3},
    3: {"reps_cap": 45, "review_target": 6},
    4: {"reps_cap": 45, "review_target": 8},
    5: {"reps_cap": 55, "review_target": 10},
}
# Review lessons are word-heavy by design — they get extra reps headroom.
REVIEW_CAP_BONUS = 12
# Hearts taught this many lessons before the frontier need this many
# re-reads in LATER lessons.
HEART_RULE = [(5, 2), (2, 1)]  # (min lessons since taught, re-reads needed)


def load_prons(words):
    path = os.path.join(ROOT, "..", "..", "phonics-tool", "cmudict-0.7b.txt")
    prons = {}
    if not os.path.exists(path):
        return prons
    needed = set(words)
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


def main():
    cur = load()

    top500 = []
    with open(os.path.join(ROOT, "data", "cpb-top-500.csv")) as f:
        for row in csv.DictReader(f):
            top500.append(row["word"].lower())
    rank = {w: i + 1 for i, w in enumerate(top500)}

    # read-practice per lesson (vetted files only — same window as load_used)
    lesson_module = {l["n"]: l["module"] for l in cur.lessons}
    lesson_title = {l["n"]: l["title"] for l in cur.lessons}
    per_lesson = {}   # n -> read Counter
    for n, _counts, read_counts, _slides in load_lesson_files(ROOT):
        if lesson_module.get(n, 99) > 5:
            continue
        per_lesson[n] = read_counts
    frontier = max(per_lesson) if per_lesson else 0

    seen_in = defaultdict(set)   # word -> lessons where read
    reps = Counter()
    first_read = {}
    for n in sorted(per_lesson):
        for w, c in per_lesson[n].items():
            seen_in[w].add(n)
            reps[w] += c
            first_read.setdefault(w, n)

    # sound-verified availability: max(spelling tiling, CMU alignment)
    heart_lessons = {}
    for l in cur.lessons:
        for w in l["heart"]:
            heart_lessons.setdefault(w.lower(), l["n"])
    candidates = [w for w in top500 if w not in seen_in]
    prons = load_prons(candidates)
    corr = cmu_correspondences(cur)

    def sound_avail(word):
        spell, _ = cur.first_available(word)
        if spell is None:
            return None
        if word in heart_lessons:
            return spell
        cmu = cmu_readable(word, prons, corr, heart_lessons)
        if cmu is None:
            return None
        return max(spell, cmu)

    # 1. heart retention -----------------------------------------------------
    hearts = []
    for l in cur.lessons:
        if l["n"] > frontier:
            continue
        for w in l["heart"]:
            w = w.lower()
            later = sorted(x for x in seen_in.get(w, ()) if x > l["n"])
            age = frontier - l["n"]
            need = 0
            for min_age, n_need in HEART_RULE:
                if age >= min_age:
                    need = n_need
                    break
            hearts.append({
                "word": w, "taught": l["n"], "later": later,
                "need": need, "reps": reps[w],
                "ok": len(later) >= need,
            })
    heart_fail = [h for h in hearts if not h["ok"]]

    # 2. backfill queue ------------------------------------------------------
    backfill = []
    for w in candidates:
        a = sound_avail(w)
        if a is not None and a <= frontier:
            backfill.append({"word": w, "rank": rank[w], "avail": a,
                             "waiting": frontier - a})
    backfill.sort(key=lambda b: b["rank"])

    # 3. one-shot words ------------------------------------------------------
    one_shot = []
    for w in top500:
        if len(seen_in.get(w, ())) == 1:
            n = next(iter(seen_in[w]))
            if frontier - n >= 5:
                one_shot.append({"word": w, "rank": rank[w], "lesson": n,
                                 "reps": reps[w]})
    one_shot.sort(key=lambda o: o["rank"])

    # 4. per-lesson load -----------------------------------------------------
    load_rows = []
    for n in sorted(per_lesson):
        c = per_lesson[n]
        distinct = set(c)
        review = {w for w in distinct if first_read.get(w, n) < n}
        b = BUDGET[lesson_module[n]]
        cap = b["reps_cap"]
        if "review" in lesson_title[n].lower():
            cap += REVIEW_CAP_BONUS
        load_rows.append({
            "n": n, "title": lesson_title[n], "module": lesson_module[n],
            "reps": sum(c.values()), "distinct": len(distinct),
            "review": len(review), "target": b["review_target"],
            "cap": cap,
            "over": sum(c.values()) > cap,
            "under": (b["review_target"] > 0
                      and len(review) < b["review_target"]),
        })

    write_html(frontier, hearts, heart_fail, backfill, one_shot, load_rows)

    over = [r for r in load_rows if r["over"]]
    under = [r for r in load_rows if r["under"]]
    print(f"review queue @ L{frontier}: "
          f"hearts needing review: {len(heart_fail)}, "
          f"backfill queue: {len(backfill)}, "
          f"one-shot words: {len(one_shot)}")
    print(f"lesson load: {len(over)} over reps cap, "
          f"{len(under)} under review target")
    if heart_fail:
        print("  hearts:", ", ".join(
            f"{h['word']}(L{h['taught']},{len(h['later'])}/{h['need']})"
            for h in heart_fail))


def write_html(frontier, hearts, heart_fail, backfill, one_shot, load_rows):
    def table(headers, rows):
        h = "".join(f"<th>{x}</th>" for x in headers)
        b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
                    for r in rows)
        return f"<table><tr>{h}</tr>{b}</table>"

    heart_rows = []
    for h in sorted(hearts, key=lambda x: (x["ok"], x["taught"])):
        status = ("<span class='ok'>ok</span>" if h["ok"]
                  else "<b class='no'>needs review</b>")
        later = ", ".join(f"L{x}" for x in h["later"]) or "—"
        heart_rows.append((h["word"], f"L{h['taught']}", h["reps"],
                           later, f"{len(h['later'])}/{h['need']}", status))

    bf_rows = [(b["rank"], b["word"], f"L{b['avail']}", b["waiting"])
               for b in backfill]
    os_rows = [(o["rank"], o["word"], f"L{o['lesson']}", o["reps"])
               for o in one_shot]
    ld_rows = []
    for r in load_rows:
        flags = []
        if r["over"]:
            flags.append("<b class='no'>over cap</b>")
        if r["under"]:
            flags.append("<span class='warn'>under target</span>")
        ld_rows.append((f"L{r['n']}", r["title"], f"M{r['module']}",
                        f"{r['reps']} / {r['cap']}", r["distinct"],
                        f"{r['review']} / {r['target'] or '—'}",
                        " ".join(flags)))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Learn to Read — Review Queue</title>
<style>
  body {{ font-family: ui-sans-serif, -apple-system, sans-serif; font-size: 13px;
         color: #212622; background: #faf9f5; margin: 24px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  h2 {{ font-size: 16px; margin: 28px 0 6px; }}
  p.sub {{ color: #59635c; margin: 0 0 16px; max-width: 760px; }}
  table {{ border-collapse: collapse; background: #fff; }}
  th, td {{ border: 1px solid #e6e2d8; padding: 3px 10px; text-align: left;
            font-variant-numeric: tabular-nums; }}
  th {{ background: #fcfbf8; font-size: 11px; color: #8a938c; }}
  .ok {{ color: #2e6f52; }}
  .no {{ color: #cf3f3f; }}
  .warn {{ color: #b07a1f; }}
</style>
</head>
<body>
<h1>Review Queue</h1>
<p class="sub">Which known words need more practice, as of lesson {frontier}.
All lists are sound-verified (spelling tiling AND CMUdict pronunciation) so a
spelling-only false positive like <i>says</i> or <i>day</i> can never be
recommended. Module 1 is exempt from review pressure — everything is new and
every word is slow. Regenerate with
<code>python3 scripts/build-review-queue.py</code>.</p>

<h2>1 · Heart retention ({len(heart_fail)} need review)</h2>
<p class="sub">Hearts are memorized words — they need spaced retrieval most.
Rule: taught ≥{HEART_RULE[0][0]} lessons ago → read in ≥{HEART_RULE[0][1]}
later lessons; taught ≥{HEART_RULE[1][0]} ago → ≥{HEART_RULE[1][1]}.</p>
{table(["word", "taught", "reps", "later lessons", "re-reads", "status"], heart_rows)}

<h2>2 · Backfill queue ({len(backfill)} words)</h2>
<p class="sub">Top-500 words decodable with taught code but never read in any
lesson. Highest rank first — the shopping list for review-lesson word chains
and fluency sentences. "waiting" = lessons since the word became decodable.</p>
{table(["rank", "word", "decodable since", "waiting"], bf_rows)}

<h2>3 · One-shot words ({len(one_shot)} words)</h2>
<p class="sub">Top-500 words read in exactly one lesson and not seen in the
last 5 lessons.</p>
{table(["rank", "word", "only lesson", "reps"], os_rows)}

<h2>4 · Per-lesson load</h2>
<p class="sub">Overload guard: total read-word reps vs the module's cap, and
distinct review words (read before, revisited here) vs the module's target.</p>
{table(["lesson", "title", "module", "reps / cap", "distinct words",
        "review / target", "flags"], ld_rows)}
</body>
</html>"""
    out = os.path.join(ROOT, "REVIEW_QUEUE.html")
    open(out, "w").write(html)


if __name__ == "__main__":
    main()
