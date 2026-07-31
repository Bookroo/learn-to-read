#!/usr/bin/env python3
"""Generate MODULE_ORDER_PROPOSED.html from data/curriculum.json.

curriculum.json is the source of truth for the lesson order. This script
renders the full doc — lesson tables, Concepts & Exercises reference, Dolch
coverage, the contractions rule, the leftover top-500 table, and the CPB
top-3,000 appendix. Everything derivable is derived:

  - lesson numbers come from list order,
  - reference-table "first introduced" numbers come from the lesson intros,
  - the contractions rule points at wherever the contractions lesson sits,
  - leftover-table suggestions reference lessons by slug,
  - Dolch coverage is computed from examples + heart words.

Usage: python3 scripts/build-module-order.py     # rewrites the doc in place
"""

import csv
import html as html_mod
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from availability import example_words, normalize_lessons  # noqa: E402

TAG_LABELS = {
    "letter": "Letter", "pattern": "Pattern", "concept": "Concept",
    "strategy": "Strategy", "morph": "Word Parts", "heart": "Heart Words",
    "fluency": "Fluency", "review": "Review",
}

CSS = """
      :root {
        --paper: #faf9f5;
        --card: #ffffff;
        --ink: #212622;
        --ink-soft: #59635c;
        --ink-faint: #8a938c;
        --accent: #2e6f52;
        --accent-deep: #22553f;
        --accent-soft: #e8f1ea;
        --accent-line: #cadfd1;
        --line: #e6e2d8;
        --line-strong: #d6d1c4;

        --tag-letter: #2c6fb0;
        --tag-letter-soft: #e8f0f8;
        --tag-pattern: #2e6f52;
        --tag-pattern-soft: #e8f1ea;
        --tag-concept: #7c4fa8;
        --tag-concept-soft: #f0e9f7;
        --tag-strategy: #b3791f;
        --tag-strategy-soft: #f7eeda;
        --tag-morph: #94643a;
        --tag-morph-soft: #f3ece2;
        --tag-heart: #bb432b;
        --tag-heart-soft: #f8e9e5;
        --tag-fluency: #0f766e;
        --tag-fluency-soft: #e2f1ef;
        --tag-review: #6d7a73;
        --tag-review-soft: #eceeeb;
        --dolch: #cf3f7c;

        --radius: 12px;
        --radius-sm: 8px;
        --shadow: 0 1px 2px rgba(30, 40, 34, 0.04),
          0 6px 20px rgba(30, 40, 34, 0.05);
      }

      * { box-sizing: border-box; }
      html { scroll-behavior: smooth; }

      body {
        margin: 0;
        background: var(--paper);
        color: var(--ink);
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont,
          "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 15.5px;
        line-height: 1.55;
        -webkit-font-smoothing: antialiased;
      }

      .wrap { max-width: 1060px; margin: 0 auto; padding: 48px 24px 96px; }

      header.doc h1 {
        font-size: 30px; line-height: 1.2; margin: 0 0 6px;
        letter-spacing: -0.01em;
      }
      header.doc .meta { color: var(--ink-faint); font-size: 13px; margin-top: 10px; }

      .rules {
        margin: 28px 0 8px; display: grid; gap: 12px;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      }
      .rule {
        background: var(--card); border: 1px solid var(--line);
        border-radius: var(--radius); padding: 14px 16px;
        box-shadow: var(--shadow); font-size: 14px;
      }
      .rule b { display: block; margin-bottom: 2px; color: var(--accent-deep); }
      .rule span { color: var(--ink-soft); }

      section.module { margin-top: 44px; }
      .module-head {
        display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;
        margin-bottom: 4px;
      }
      .module-head h2 { font-size: 21px; margin: 0; letter-spacing: -0.01em; }
      .module-theme {
        color: var(--ink-soft); font-size: 14.5px; max-width: 780px;
        margin: 0 0 14px;
      }

      table {
        width: 100%; border-collapse: separate; border-spacing: 0;
        background: var(--card); border: 1px solid var(--line);
        border-radius: var(--radius); overflow: hidden;
        box-shadow: var(--shadow); font-size: 14px;
      }
      th {
        text-align: left; font-size: 11.5px; text-transform: uppercase;
        letter-spacing: 0.06em; color: var(--ink-faint); font-weight: 600;
        padding: 10px 12px; border-bottom: 1px solid var(--line-strong);
        background: #fcfbf8;
      }
      td { padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
      tr:last-child td { border-bottom: none; }
      td.num {
        color: var(--ink-faint); font-variant-numeric: tabular-nums;
        white-space: nowrap; width: 34px;
      }
      td.what { font-weight: 600; white-space: nowrap; }
      td.what .sub {
        display: block; font-weight: 400; color: var(--ink-soft);
        font-size: 12.5px; white-space: normal;
      }
      td.detail { color: var(--ink-soft); }
      td.examples { color: var(--ink); font-style: italic; width: 28%; }
      td.examples .words { display: block; }
      td.examples .words + .words { margin-top: 4px; }
      td.examples .example-label { font-style: normal; }
      .dolch-word { color: var(--dolch); font-weight: 600; }
      td.examples .none { color: var(--ink-faint); font-style: normal; }
      .detail-intros { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 7px; }
      .detail-intros:only-child { margin-top: 0; }
      .detail-intro,
      .reference-label {
        display: inline-block; border-radius: 999px; font-size: 11px;
        font-weight: 600; line-height: 1.35; padding: 3px 8px;
      }
      .intro-concept, .reference-concept {
        color: var(--tag-concept); background: var(--tag-concept-soft);
      }
      .intro-exercise, .reference-exercise {
        color: var(--tag-fluency); background: var(--tag-fluency-soft);
      }

      .tag {
        display: inline-block; font-size: 11px; font-weight: 600;
        letter-spacing: 0.04em; padding: 2px 8px; border-radius: 999px;
        white-space: nowrap; vertical-align: middle;
      }
      .t-letter { color: var(--tag-letter); background: var(--tag-letter-soft); }
      .t-pattern { color: var(--tag-pattern); background: var(--tag-pattern-soft); }
      .t-concept { color: var(--tag-concept); background: var(--tag-concept-soft); }
      .t-strategy { color: var(--tag-strategy); background: var(--tag-strategy-soft); }
      .t-morph { color: var(--tag-morph); background: var(--tag-morph-soft); }
      .t-heart { color: var(--tag-heart); background: var(--tag-heart-soft); }
      .t-fluency { color: var(--tag-fluency); background: var(--tag-fluency-soft); }
      .t-review { color: var(--tag-review); background: var(--tag-review-soft); }

      .note {
        background: var(--accent-soft); border: 1px solid var(--accent-line);
        border-radius: var(--radius-sm); padding: 10px 14px; font-size: 13.5px;
        color: var(--accent-deep); margin: 12px 0 0;
      }

      section.prose { margin-top: 52px; max-width: 820px; }
      section.prose h2 { font-size: 21px; margin: 0 0 12px; }
      section.prose h3 { font-size: 16px; margin: 22px 0 6px; }
      section.prose p, section.prose li { color: var(--ink-soft); font-size: 14.5px; }
      section.prose li { margin-bottom: 6px; }
      section.prose b, section.prose strong { color: var(--ink); }
      .reference-table td:first-child { width: 210px; color: var(--ink); font-weight: 600; }
      .reference-table td:nth-child(2) { width: 120px; color: var(--ink-faint); white-space: nowrap; }
      .reference-table td:last-child { color: var(--ink-soft); }

      footer {
        margin-top: 64px; color: var(--ink-faint); font-size: 12.5px;
        border-top: 1px solid var(--line); padding-top: 16px;
      }

      .freq-cols {
        columns: 5 180px; column-gap: 28px; font-size: 12.5px;
        font-variant-numeric: tabular-nums; margin-top: 16px;
      }
      .fe { display: flex; gap: 8px; padding: 1px 0; break-inside: avoid; }
      .fe .r { color: var(--ink-faint); min-width: 36px; text-align: right; }
      .fe .w { font-weight: 600; flex: 1; }
      .fe .f { color: var(--ink-faint); }
      @media (max-width: 720px) { td.what { white-space: normal; } }
"""


def esc(s):
    return html_mod.escape(str(s), quote=False)


def main():
    data = json.load(open(os.path.join(ROOT, "data", "curriculum.json")))
    lessons = normalize_lessons(data["lessons"])
    slug_to_n = {l["slug"]: l["n"] for l in lessons}
    dolch = set(data["dolch_pre_k"])

    def mark_dolch(text):
        parts = re.split(r"([A-Za-z']+)", esc(text))
        return "".join(
            f'<span class="dolch-word">{p}</span>'
            if p.lower() in dolch else p
            for p in parts)

    # ---- lesson tables, grouped by module -------------------------------
    modules_html = []
    for mod in data["modules"]:
        rows = []
        for l in lessons:
            if l["module"] != mod["n"]:
                continue
            what = esc(l["title"])
            if l["sub"]:
                what += f'<span class="sub">{esc(l["sub"])}</span>'
            tags = " ".join(
                f'<span class="tag t-{t}">{TAG_LABELS[t]}</span>'
                for t in l["tags"])
            detail = esc(l["detail"])
            if l["intros"]:
                chips = "".join(
                    f'<span class="detail-intro intro-{i["kind"]}">{esc(i["name"])}</span>'
                    for i in l["intros"])
                detail += f'<div class="detail-intros">{chips}</div>'
            groups = []
            no_dolch = l["slug"] == "lowercase-letters"
            for g in l["examples"]:
                text = esc(g) if no_dolch else mark_dolch(g)
                groups.append(f'<span class="words">{text}</span>')
            if l["heart"]:
                words = ", ".join(mark_dolch(w) for w in l["heart"])
                groups.append(
                    '<span class="words"><b class="example-label">heart words:</b> '
                    f"{words}</span>")
            examples = "".join(groups) or '<span class="none">—</span>'
            rows.append(f"""            <tr>
              <td class="num">{l['n']}</td>
              <td class="what">{what}</td>
              <td>{tags}</td>
              <td class="detail">{detail}</td>
              <td class="examples">{examples}</td>
            </tr>""")
        modules_html.append(f"""      <section class="module">
        <div class="module-head">
          <h2>Module {mod['n']} — {esc(mod['title'])}</h2>
        </div>
        <p class="module-theme">{esc(mod['theme'])}</p>
        <table>
          <thead>
            <tr><th>#</th><th>New thing</th><th></th><th>Details</th><th>Example words</th></tr>
          </thead>
          <tbody>
{chr(10).join(rows)}
          </tbody>
        </table>
      </section>""")

    # ---- reference table (first-introduced derived from intros) ---------
    def first_intro(name):
        for l in lessons:
            if any(i["name"] == name for i in l["intros"]):
                return l["n"]
        raise SystemExit(f"reference entry '{name}' never introduced by any lesson")

    ref_rows = []
    for r in sorted(data["reference"], key=lambda r: first_intro(r["name"])):
        ref_rows.append(
            "            <tr>"
            f'<td><span class="reference-label reference-{r["kind"]}">{esc(r["name"])}</span></td>'
            f'<td>Lesson {first_intro(r["name"])}</td>'
            f'<td>{esc(r["how"])}</td></tr>')

    # ---- Dolch coverage (computed) --------------------------------------
    heart_all = {w.lower() for l in lessons for w in l["heart"]}
    example_all = {w for l in lessons for w in example_words(l)}
    dolch_heart = sorted(dolch & heart_all)
    dolch_decoded = sorted((dolch & example_all) - set(dolch_heart))
    missing = dolch - set(dolch_heart) - set(dolch_decoded)
    if missing:
        raise SystemExit(f"Dolch words neither decoded nor heart: {missing}")

    def show(w):
        return "I" if w == "i" else w

    # ---- contractions rule ----------------------------------------------
    c = data["contractions"]
    contraction_n = slug_to_n["contractions"]
    rule_strong = esc(c["rule_strong"]).replace("{n}", str(contraction_n))

    # ---- leftover table (numbers derived from slugs) --------------------
    left_rows = []
    for row in data["leftover"]:
        if "slug" in row:
            sug = f'Lesson {slug_to_n[row["slug"]]} — {esc(row["note"])}'
        else:
            sug = esc(row["note"])
        left_rows.append(
            f"            <tr><td><i>{esc(row['word'])}</i></td>"
            f"<td>{row['rank']}</td><td>{sug}</td></tr>")

    # ---- appendix -------------------------------------------------------
    entries = []
    with open(os.path.join(ROOT, "data", "cpb-top-3000.csv")) as f:
        for row in csv.DictReader(f):
            entries.append(
                f'<span class="fe"><span class="r">{row["rank"]}</span>'
                f'<span class="w">{esc(row["word"])}</span>'
                f'<span class="f">{int(row["raw_freq"]):,}</span></span>')

    notes_html = "\n".join(
        f'          <li><b>{esc(r["title"])}.</b> {esc(r["text"])}</li>'
        for r in data["rules"])

    max_mod = max(m["n"] for m in data["modules"])
    doc = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Learn to Read — Proposed Lesson Order, Modules 1–{max_mod}</title>
    <style>{CSS}    </style>
  </head>
  <body>
    <div class="wrap">
      <header class="doc">
        <h1>Proposed Lesson Order — Modules 1–{max_mod}</h1>
        <p class="meta">Generated from data/curriculum.json — edit that file
        and run scripts/build-module-order.py; do not edit this HTML.</p>
      </header>

{chr(10).join(modules_html)}

      <section class="prose">
        <h2>Concepts &amp; Exercises</h2>
        <p>
          Lesson rows show what is taught. This reference explains the named
          routines and strategies used to teach and practice it. Purple marks a
          concept or strategy; teal marks an exercise or recurring routine.
        </p>
        <table class="reference-table">
          <thead>
            <tr><th>Concept or exercise</th><th>First introduced</th><th>How it works</th></tr>
          </thead>
          <tbody>
{chr(10).join(ref_rows)}
          </tbody>
        </table>
      </section>

      <section class="prose">
        <h2>Dolch Pre-K Word Coverage</h2>
        <p>
          All {len(dolch)} words are introduced in the lesson sequence.
          Decodable words appear in the example list for the lesson that makes
          them readable; irregular words appear as heart words.
        </p>
        <h3>Naturally decoded in lesson examples</h3>
        <p><i>{", ".join(show(w) for w in dolch_decoded)}</i></p>
        <h3>Introduced as heart words</h3>
        <p><i>{", ".join(show(w) for w in dolch_heart)}</i></p>
      </section>

      <section class="prose">
        <h2>Rule Before the Contractions Lesson</h2>
        <div class="note">
          <strong>{rule_strong}</strong>
          {esc(c["rule_text"])}
        </div>
        <p>{c["phrases_html"]}</p>
      </section>

      <section class="prose">
        <h2>Leftover Top-500 Words</h2>
        <p>
          These frequent words are not yet explicitly taught or listed. The
          table excludes ordinary inflections, words already decodable from the
          taught code, and most proper names. Ranks use CPB Raw Freq in
          <i>CPB(Lexicon).xlsx</i>.
        </p>
        <table>
          <thead>
            <tr><th>Word</th><th>CPB rank</th><th>Suggested lesson</th></tr>
          </thead>
          <tbody>
{chr(10).join(left_rows)}
          </tbody>
        </table>
      </section>

      <section class="prose">
        <h2>Notes</h2>
        <ul>
{notes_html}
        </ul>
      </section>

      <section class="prose" style="max-width: none">
        <h2>CPB Top 3,000 Words</h2>
        <p style="max-width: 820px">
          Rank and raw frequency from <i>CPB(Lexicon).xlsx</i>, the children's
          picture book corpus. Use this to look up how common a word is when
          choosing lesson and book words.
        </p>
        <div class="freq-cols">{"".join(entries)}</div>
      </section>

      <footer>Bookroo Learn to Read</footer>
    </div>
  </body>
</html>
"""
    out = os.path.join(ROOT, "MODULE_ORDER_PROPOSED.html")
    open(out, "w").write(doc)
    print(f"{len(lessons)} lessons, {len(ref_rows)} reference rows, "
          f"{len(dolch_decoded)} Dolch decoded + {len(dolch_heart)} heart -> {out}")


if __name__ == "__main__":
    main()
