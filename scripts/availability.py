#!/usr/bin/env python3
"""Per-lesson decodability engine for the Learn to Read curriculum.

Reads data/curriculum.json (see extract-curriculum.py) and data/cpb-top-3000.csv
and answers: at each lesson, which graphemes are taught and which words are
newly available? A word is available when it is a taught heart word or when its
spelling can be tiled with taught graphemes, subject to strategy gates
(suffixes, Magic E, two-/three-syllable reading, contractions, ...).

Tiling is spelling-side and deliberately optimistic; words that tile but are
not honestly decodable belong in NOT_DECODABLE below (most are heart words
already, which take priority anyway).

Usage:
  python3 scripts/availability.py            # writes LESSON_AVAILABILITY.html
  python3 scripts/availability.py --check    # verify lesson examples decodable
  python3 scripts/availability.py --cmu      # CMUdict pronunciation audit:
                                             # flags words the spelling engine
                                             # calls readable but whose real
                                             # pronunciation never aligns

Importable: load() -> Curriculum with .first_available(word).
"""

import csv
import json
import os
import re
import sys
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VOWEL_LETTERS = set("aeiou")

# Spellings that count as one vowel unit (beat) when tiled.
VOWEL_UNITS = {
    "a", "e", "i", "o", "u", "y",
    "ee", "ea", "ai", "ay", "oa", "oo", "aw", "au", "ou", "ow", "oi", "oy",
    "ew", "ue", "ie", "igh", "eigh", "oe", "ey",
    "ar", "or", "er", "ir", "ur", "are", "air", "ear", "ore",
    "ung", "ong", "unk", "onk", "ing", "ink", "ank", "ang",
    "old", "ost", "ind", "ild", "all", "al", "aught",
}

# Words that tile with taught graphemes but are not honestly decodable at that
# point (irregular pronunciation) and are not taught as heart words. Value is
# the lesson that earns them, or None for "treat as unavailable".
NOT_DECODABLE = {
    "front": None, "wash": None, "watch": None, "wasp": None,
    "swallow": None, "swallowed": None, "swan": None, "squash": None,
    "pint": None, "both": None, "most-": None,
}

SUFFIXES = [
    # (suffix, gate)
    ("ing", "suffix-ing"),
    ("es", "suffix-es"),
    ("ed", "suffix-ed"),
    ("est", "suffix-er-est"),
    ("er", "suffix-er-est"),
    ("s", "suffix-s"),
]

CONTRACTION_ENDINGS = ["n't", "'ll", "'re", "'ve", "'s", "'m", "'d", "'t"]

# Letter pairs that are (virtually) always one spelling unit in English: a
# tile boundary may never fall between them, so e.g. night cannot tile as
# n·i·g·h·t before igh is taught, nor sing as s·i·n·g before -ing.
NO_SPLIT = {"sh", "ch", "th", "wh", "ph", "gh", "ck", "ng", "nk"}
NO_SPLIT_INITIAL = {"kn", "wr"}   # only as word-initial pairs
NO_SPLIT_FINAL = {"mb"}           # only as word-final pairs

# Short function words that may serve as compound parts (in·to, may·be).
SHORT_COMPOUND_PARTS = {"in", "to", "up", "on", "at", "be", "my", "no", "go",
                        "so", "he", "we", "me", "do", "an", "or", "out"}


class State:
    """Cumulative taught code up to and including a lesson."""

    def __init__(self):
        self.graphemes = set()      # taught spellings
        self.vowel_e = set()        # vowels with a taught V_e pattern
        self.gates = set()
        self.heart = set()

    def clone(self):
        s = State()
        s.graphemes = set(self.graphemes)
        s.vowel_e = set(self.vowel_e)
        s.gates = set(self.gates)
        s.heart = set(self.heart)
        return s


class Curriculum:
    def __init__(self, lessons, ranks):
        self.lessons = lessons          # curriculum.json lesson dicts
        self.ranks = ranks              # word -> cpb rank
        # Known real words: suffix-stripped bases must appear here, so that
        # e.g. "making" is not accepted via the nonword base "mak".
        self.known = set(ranks)
        for l in lessons:
            for w in l["heart"]:
                self.known.add(w.lower())
            for w in example_words(l):
                self.known.add(w)
        self.states = []                # states[i] = code after lesson i+1
        state = State()
        for l in lessons:
            state = state.clone()
            for g, _p in l["graphemes"]:
                if g.endswith("_e"):
                    state.vowel_e.add(g[0])
                else:
                    state.graphemes.add(g)
            state.gates.update(l["gates"])
            state.heart.update(w.lower() for w in l["heart"])
            self.states.append(state)

    # -- tiling ------------------------------------------------------------

    def _tile_units(self, word, state):
        """Min vowel units to tile word with taught code, or None."""
        n = len(word)
        spellings = sorted(state.graphemes, key=len, reverse=True)
        INF = 99

        def legal_boundary(j):
            """May a tile boundary fall before position j?"""
            if j <= 0 or j >= n:
                return True
            pair = word[j - 1 : j + 1]
            if pair in NO_SPLIT:
                return False
            if pair in NO_SPLIT_INITIAL and j == 1:
                return False
            if pair in NO_SPLIT_FINAL and j == n - 1:
                return False
            # doubled consonants are one unit (ss taught, or doubling rules)
            if pair[0] == pair[1] and pair[0] not in VOWEL_LETTERS:
                return False
            # adjacent vowel letters are a team, not two short vowels (rain)
            # — except the u of qu, which is consonant territory (quit)
            if (pair[0] in VOWEL_LETTERS and pair[1] in VOWEL_LETTERS
                    and not (pair[0] == "u" and j >= 2 and word[j - 2] == "q")):
                return False
            # a vowel before r is r-controlled — must use ar/or/er/... (her)
            if pair[0] in VOWEL_LETTERS and pair[1] == "r":
                return False
            # vowel + w acting as a glide must be a team (down, saw, new) —
            # unless w starts a new syllable before a vowel (away)
            if (pair[0] in VOWEL_LETTERS and pair[1] == "w"
                    and (j + 1 == n or word[j + 1] not in VOWEL_LETTERS)):
                return False
            return True

        @lru_cache(maxsize=None)
        def best(i):
            if i == n:
                return 0
            res = INF
            # plain graphemes
            for g in spellings:
                if word.startswith(g, i) and legal_boundary(i + len(g)):
                    if g in ("ng", "nk"):  # handled by the after-o/u branch
                        continue
                    # y: vowel only at word end (needs vowel-y), else consonant
                    is_vowel = g in VOWEL_UNITS
                    if g == "y":
                        if i == n - 1:
                            if "vowel-y" not in state.gates:
                                continue
                        else:
                            is_vowel = False
                    # a final lone short-vowel letter reads long/open — that
                    # discovery is the Meet the Vowels lesson
                    if (g in VOWEL_LETTERS and i == n - 1
                            and "open-final" not in state.gates):
                        continue
                    # final open e only in tiny words (he, she, we) — a long
                    # word ending in e is silent-e territory, not open e
                    if g == "e" and i == n - 1 and n > 3:
                        continue
                    sub = best(i + len(g))
                    res = min(res, sub + (1 if is_vowel else 0))
            # Magic E: V + single consonant + final e
            if ("magic-e" in state.gates and i + 2 < n and word[i] in state.vowel_e
                    and i + 3 == n and word[i + 2] == "e"):
                c = word[i + 1]
                ok = (c in state.graphemes and c not in VOWEL_LETTERS)
                if c == "c":
                    ok = "soft-c" in state.gates
                if c == "g":
                    ok = "soft-g" in state.gates
                if ok:
                    res = min(res, 1)
            # soft c / g before e or final -ce / -ge chunks (face via a_e is
            # covered above; this covers e.g. "cell", "gem")
            if word[i] == "c" and "soft-c" in state.gates and i + 1 < n and word[i + 1] in "e":
                res = min(res, best(i + 1))
            if word[i] == "g" and "soft-g" in state.gates and i + 1 < n and word[i + 1] in "e":
                res = min(res, best(i + 1))
            # doubled consonant (rabbit, muffin) once two-syllable reading is on
            if ("two-syllable" in state.gates and i + 1 < n
                    and word[i] == word[i + 1] and word[i] not in VOWEL_LETTERS
                    and word[i] in state.graphemes and legal_boundary(i + 2)):
                sub = best(i + 2)
                res = min(res, sub)
            # consonant-le final syllable (ap·ple — le after any consonant)
            if ("consonant-le" in state.gates and i == n - 2
                    and word.endswith("le") and i >= 1
                    and word[i - 1] not in VOWEL_LETTERS):
                res = min(res, 1)
            # ng/nk read as plain consonants only after o or u sounds
            # (song, young, honk) — after a or i they are glued chunks
            for tail in ("ng", "nk"):
                if (tail in state.graphemes and word.startswith(tail, i)
                        and i >= 1 and word[i - 1] in "ou"
                        and legal_boundary(i + 2)):
                    res = min(res, best(i + 2))
            # silent final e after s/z/v/c/g (house, because, believe) —
            # part of the Magic E convention: English words don't end in v/z/s
            if ("magic-e" in state.gates and i == n - 1 and word[i] == "e"
                    and n >= 2 and word[i - 1] in "szvcg"):
                res = min(res, 0)
            return res

        u = best(0)
        return None if u >= INF else u

    def _available(self, word, state):
        """Is word available under state? Returns (ok, how)."""
        w = word.lower()
        if w in state.heart:
            return True, "heart"
        if w in NOT_DECODABLE:
            return False, "excluded"
        if "'" in w:
            if "contractions" not in state.gates:
                return False, ""
            for end in CONTRACTION_ENDINGS:
                if w.endswith(end):
                    base = w[: -len(end)]
                    ok, _ = self._available(base, state)
                    if ok:
                        return True, "contraction"
            return False, ""
        units = self._tile_units(w, state)
        if units is not None and self._syllable_ok(units, state):
            # multi-beat words ending in -ing/-ed/-es must earn it as base +
            # suffix (or a compound below), not by tiling around the ending
            if not (units >= 2 and (w.endswith("ing") or w.endswith("ed")
                                    or w.endswith("es"))):
                return True, "decode"
        # suffix morphology
        for suf, gate in SUFFIXES:
            if gate not in state.gates or not w.endswith(suf) or len(w) <= len(suf):
                continue
            base = w[: -len(suf)]
            candidates = [base]
            if "drop-e" in state.gates:
                candidates.append(base + "e")
            if ("doubling" in state.gates and len(base) >= 2
                    and base[-1] == base[-2] and base[-1] not in VOWEL_LETTERS):
                candidates.append(base[:-1])
            for cand in candidates:
                if cand not in self.known:
                    continue
                if cand in state.heart:
                    return True, f"heart+{suf}"
                cu = self._tile_units(cand, state)
                if cu is not None and self._syllable_ok(cu, state):
                    return True, f"decode+{suf}"
        # compound of two known readable words (sunset, something); parts
        # must be substantial words — "ma·king" is not a compound
        if "two-syllable" in state.gates:
            for i in range(2, len(w) - 1):
                a, b = w[:i], w[i:]
                if a not in self.known or b not in self.known:
                    continue
                if not all(len(p) >= 3 or p in SHORT_COMPOUND_PARTS
                           for p in (a, b)):
                    continue
                ua = 0 if a in state.heart else self._tile_units(a, state)
                ub = 0 if b in state.heart else self._tile_units(b, state)
                if (ua is not None and ub is not None
                        and self._syllable_ok(max(2, ua + ub), state)):
                    return True, "compound"
        return False, ""

    @staticmethod
    def _syllable_ok(units, state):
        if units >= 3:
            return "three-syllable" in state.gates
        if units == 2:
            return "two-syllable" in state.gates
        return True

    # -- public ------------------------------------------------------------

    def first_available(self, word):
        """(lesson_number, how) or (None, '')."""
        for i, state in enumerate(self.states):
            ok, how = self._available(word, state)
            if ok:
                return i + 1, how
        return None, ""

    def availability_by_lesson(self, words):
        """{lesson_number: [(word, rank, how), ...]} for newly available words."""
        out = {l["n"]: [] for l in self.lessons}
        for w in words:
            n, how = self.first_available(w)
            if n is not None:
                out[n].append((w, self.ranks.get(w), how))
        for n in out:
            out[n].sort(key=lambda t: (t[1] is None, t[1], t[0]))
        return out


def load():
    lessons = json.load(open(os.path.join(ROOT, "data", "curriculum.json")))["lessons"]
    ranks = {}
    with open(os.path.join(ROOT, "data", "cpb-top-3000.csv")) as f:
        for row in csv.DictReader(f):
            ranks[row["word"]] = int(row["rank"])
    cur = Curriculum(lessons, ranks)
    # System dictionary widens the known-word set for suffix bases and
    # compound parts (lowercase entries only — skips proper nouns).
    dict_path = "/usr/share/dict/words"
    if os.path.exists(dict_path):
        with open(dict_path) as f:
            cur.known.update(
                w for w in (line.strip() for line in f)
                if len(w) >= 2 and w.isalpha() and w == w.lower())
    return cur


# ---------------------------------------------------------------------------


def example_words(lesson):
    """Tokenize a lesson's example group strings into plain words."""
    if lesson["slug"] == "lowercase-letters":  # examples are letter lists
        return []
    out = []
    for group in lesson["examples"]:
        for chunk in re.split(r"[;,]", group):
            for part in chunk.split("→"):
                part = re.sub(r"\s*/.*$", "", part).strip().lower()
                part = part.replace("’", "'")
                if re.fullmatch(r"[a-z]+(?:'[a-z]+)*", part):
                    out.append(part)
    return out


def check(cur):
    """Every lesson example should be available at its own lesson."""
    bad = []
    for l in cur.lessons:
        state = cur.states[l["n"] - 1]
        for word in example_words(l):
            ok, _ = cur._available(word, state)
            if not ok:
                bad.append((l["n"], l["slug"], word))
    if bad:
        print(f"{len(bad)} example words NOT available at their lesson:")
        for n, slug, w in bad:
            print(f"  L{n:>3} {slug:32} {w}")
    else:
        print("all lesson examples available at their lesson ✓")
    return bad


def esc_js(s):
    return str(s).replace("\\", "\\\\").replace("'", "\\'").replace('"', "&quot;")


def load_used(cur):
    """Practice data from drafted Module 1 lesson files only (later modules
    are not cleaned up yet). Returns ({curriculum_n: Counter}, issues) where
    issues lists (curriculum_n, word, slide_types, avail) for words READ
    before they are readable."""
    from practice_counts import load_lesson_files, load_lesson_map
    lesson_map = load_lesson_map(ROOT)
    slug_to_lesson = {l["slug"]: l for l in cur.lessons}
    used = {}
    issues = []
    for number, counts, _read, reading_slides in load_lesson_files(ROOT):
        slug = lesson_map.get(number)
        lesson = slug_to_lesson.get(slug) if slug else None
        if lesson is None or lesson["module"] != 1:
            continue
        n = lesson["n"]
        used[n] = counts
        for w, types in reading_slides.items():
            avail, _ = cur.first_available(w)
            if avail is None or avail > n:
                issues.append((n, w, sorted(set(types)), avail))
    return used, issues


def build_html(cur):
    counts = cur.availability_by_lesson(list(cur.ranks))
    used, issues = load_used(cur)
    used_any = set()
    for c in used.values():
        used_any.update(c)

    # word data for the modal: [word, rank, first-available lesson, used]
    word_data = sorted(
        ((w, cur.ranks.get(w), n) for n, lst in counts.items() for w, _, _ in lst),
        key=lambda t: (t[1] is None, t[1], t[0]))
    words_json = json.dumps(
        [[w, r, n, 1 if w in used_any else 0] for w, r, n in word_data],
        ensure_ascii=False, separators=(",", ":"))

    total = 0
    body = []
    INLINE = 18
    for l in cur.lessons:
        new = counts[l["n"]]
        total += len(new)
        chips = " ".join(
            f"<span class='g'>{g} <i>{p}</i></span>" for g, p in l["graphemes"])
        gates = " ".join(f"<span class='gate'>{x}</span>" for x in l["gates"])
        heart = ", ".join(l["heart"])
        words = " ".join(
            f"<span class='w{' h' if how.startswith('heart') else ''}"
            f"{' u' if w in used_any else ''}'"
            f" title='{'rank ' + str(rank) if rank else 'unranked'} · {how}'>"
            f"{w}{'<b>✓</b>' if w in used_any else ''}</span>"
            for w, rank, how in new[:INLINE])
        more = (f" <button class='more' onclick=\"openModal({l['n']}, "
                f"'Lesson {l['n']} — {esc_js(l['title'])}')\">all {total} available →</button>")
        lesson_used = used.get(l["n"])
        if lesson_used is not None:
            used_words = []
            for w, c in sorted(lesson_used.items(),
                               key=lambda t: (cur.ranks.get(t[0]) is None,
                                              cur.ranks.get(t[0]), t[0])):
                avail, _ = cur.first_available(w)
                early = avail is None or avail > l["n"]
                sup = f"<i>×{c}</i>" if c > 1 else ""
                used_words.append(
                    f"<span class='w{' bad' if early else ''}'"
                    f" title='{'rank ' + str(cur.ranks[w]) if w in cur.ranks else 'unranked'}"
                    f" · available L{avail if avail else '—'}'>{w}{sup}</span>")
            used_html = f"<span class='count'>{len(lesson_used)}</span>" + " ".join(used_words)
        else:
            used_html = "<span class='none'>—</span>"
        body.append(f"""
<tr>
  <td class="n">{l['n']}</td>
  <td class="t">{l['title']}<div class="sub">{l['sub']}</div></td>
  <td class="code">{chips} {gates}</td>
  <td class="heart">{heart}</td>
  <td class="new"><span class="count">{len(new)}</span>{words}{more}</td>
  <td class="used">{used_html}</td>
</tr>""")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Learn to Read — Lesson Availability</title>
<style>
  body {{ font-family: ui-sans-serif, -apple-system, sans-serif; font-size: 13.5px;
         color: #212622; background: #faf9f5; margin: 24px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  p.sub {{ color: #59635c; margin: 0 0 16px; max-width: 760px; }}
  table {{ border-collapse: collapse; background: #fff; width: 100%; }}
  th, td {{ border: 1px solid #e6e2d8; padding: 6px 9px; text-align: left;
            vertical-align: top; }}
  th {{ position: sticky; top: 0; background: #fcfbf8; font-size: 11.5px;
        color: #8a938c; }}
  td.n {{ font-weight: 700; color: #8a938c; text-align: right; }}
  td.t {{ font-weight: 650; white-space: nowrap; }}
  td.t .sub {{ font-weight: 400; color: #8a938c; font-size: 11.5px; }}
  .g {{ display: inline-block; background: #eef4f0; color: #2e6f52;
        border-radius: 6px; padding: 1px 7px; margin: 1px; font-weight: 650;
        white-space: nowrap; }}
  .g i {{ color: #7fa290; font-style: normal; font-weight: 500; font-size: 11.5px; }}
  .gate {{ display: inline-block; background: #f3eefa; color: #6a4fa3;
           border-radius: 6px; padding: 1px 7px; margin: 1px; font-size: 11.5px;
           font-weight: 600; }}
  td.heart {{ color: #cf3f7c; font-weight: 600; max-width: 130px; }}
  td.new {{ line-height: 1.9; }}
  .count {{ display: inline-block; min-width: 26px; margin-right: 8px;
            color: #8a938c; font-weight: 700; font-variant-numeric: tabular-nums; }}
  .w {{ background: #f4f2ec; border-radius: 5px; padding: 1px 6px; margin: 1px;
        white-space: nowrap; display: inline-block; }}
  .w.h {{ background: #fbeef4; color: #cf3f7c; }}
  .w.u b {{ color: #2e6f52; font-weight: 700; margin-left: 2px; }}
  .w.bad {{ background: #fdecec; color: #b3382c; font-weight: 600; }}
  .w i {{ color: #8a938c; font-style: normal; font-size: 11px; }}
  .more {{ color: #2e6f52; font-size: 12px; background: none; border: none;
           cursor: pointer; text-decoration: underline; padding: 0; }}
  td.used {{ line-height: 1.9; min-width: 180px; }}
  dialog {{ border: 1px solid #d6d1c4; border-radius: 12px; padding: 0;
            max-width: 860px; width: 90vw; max-height: 80vh; }}
  dialog::backdrop {{ background: rgba(30, 40, 34, 0.35); }}
  .dlg-head {{ display: flex; justify-content: space-between; align-items: center;
               padding: 14px 18px; border-bottom: 1px solid #e6e2d8;
               position: sticky; top: 0; background: #fff; }}
  .dlg-head h2 {{ font-size: 16px; margin: 0; }}
  .dlg-head button {{ background: none; border: none; font-size: 20px;
                      cursor: pointer; color: #8a938c; }}
  .dlg-body {{ padding: 14px 18px 18px; overflow: auto; line-height: 2.1;
               max-height: calc(80vh - 60px); }}
  .dlg-body .legend {{ color: #8a938c; font-size: 12px; margin-bottom: 10px;
                       line-height: 1.5; }}
</style>
</head>
<body>
<h1>Lesson Availability</h1>
<p class="sub">For each lesson: the grapheme–phoneme code and strategy gates it
unlocks, its heart words, the CPB top-3,000 words that become readable at that
lesson (first {INLINE} shown by rank; pink = via heart word;
<b style="color:#2e6f52">✓</b> = used in a drafted lesson), and the words the
drafted lesson actually practices (<span style="color:#b3382c">red</span> =
practiced before readable). Used-word data covers Module 1 files only — later
drafts aren't cleaned up yet. Click “all N available” for the full word bank
with ranks. Generated from <code>data/curriculum.json</code> — regenerate with
<code>python3 scripts/availability.py</code>.</p>
<table>
<tr><th>#</th><th>Lesson</th><th>New code</th><th>Heart words</th>
<th>Available words</th><th>Used words</th></tr>
{''.join(body)}
</table>
<dialog id="dlg">
  <div class="dlg-head"><h2 id="dlg-title"></h2>
    <button onclick="document.getElementById('dlg').close()">✕</button></div>
  <div class="dlg-body" id="dlg-body"></div>
</dialog>
<script>
const WORDS = {words_json};
function openModal(n, label) {{
  const items = WORDS.filter(w => w[2] <= n);
  document.getElementById('dlg-title').textContent =
    label + ' — ' + items.length + ' words available';
  document.getElementById('dlg-body').innerHTML =
    '<div class="legend">Sorted by CPB rank. <b style="color:#2e6f52">✓</b> = ' +
    'used in a drafted lesson (Module 1 files only). Number = CPB rank.</div>' +
    items.map(([w, r, a, u]) =>
      '<span class="w' + (u ? ' u' : '') + '" title="available at L' + a + '">' +
      '<i>' + (r ?? '·') + '</i> ' + w + (u ? '<b>✓</b>' : '') + '</span>'
    ).join(' ');
  document.getElementById('dlg').showModal();
}}
</script>
</body>
</html>"""
    out = os.path.join(ROOT, "LESSON_AVAILABILITY.html")
    open(out, "w").write(html)
    covered = sum(len(v) for v in counts.values())
    print(f"wrote {out}")
    print(f"top-3000 coverage by Lesson 107: {covered}/3000")


# ---------------------------------------------------------------------------
# CMUdict audit — a second, pronunciation-aware readability model. For each
# word it asks: can some segmentation of the spelling into taught graphemes
# spell out one of the word's real pronunciations? Correspondences are
# GENERATED from curriculum.json (keyed by the grapheme's spelling + phoneme
# note), so this table can never drift from the lesson order.
# ---------------------------------------------------------------------------

ARPA = {
    ("m", "/m/"): [("M",)], ("a", "/ă/"): [("AE",)], ("t", "/t/"): [("T",)],
    ("s", "/s/"): [("S",)], ("s", "/z/"): [("Z",)], ("p", "/p/"): [("P",)],
    ("i", "/ĭ/"): [("IH",)], ("n", "/n/"): [("N",)], ("d", "/d/"): [("D",)],
    ("o", "/ŏ/"): [("AA",), ("AO",)], ("b", "/b/"): [("B",)],
    ("g", "/g/"): [("G",)], ("e", "/ĕ/"): [("EH",)], ("h", "/h/"): [("HH",)],
    ("l", "/l/"): [("L",)], ("c", "/k/"): [("K",)], ("u", "/ŭ/"): [("AH",)],
    ("r", "/r/"): [("R",)], ("z", "/z/"): [("Z",)],
    ("sh", "/sh/"): [("SH",)], ("ch", "/ch/"): [("CH",)],
    ("tch", "/ch/"): [("CH",)], ("y", "/y/"): [("Y",)],
    ("k", "/k/"): [("K",)], ("ck", "/k/"): [("K",)],
    ("qu", "/kw/"): [("K", "W")], ("f", "/f/"): [("F",)],
    ("ff", "/f/"): [("F",)], ("ll", "/l/"): [("L",)],
    ("ss", "/s/"): [("S",)], ("zz", "/z/"): [("Z",)],
    ("th", "/th/ /t͟h/"): [("TH",), ("DH",)],
    ("w", "/w/"): [("W",)], ("wh", "/w/"): [("W",)],
    ("ung", "/ŭng/"): [("AH", "NG")],
    ("ong", "/ŏng/"): [("AO", "NG"), ("AA", "NG")],
    ("unk", "/ŭnk/"): [("AH", "NG", "K")],
    ("onk", "/ŏnk/"): [("AA", "NG", "K"), ("AO", "NG", "K")],
    ("ng", "/ng/"): [("NG",)], ("nk", "/nk/"): [("NG", "K")],
    ("ing", "/ing/"): [("IH", "NG")],
    ("e", "/ē/ open"): [("IY",)], ("o", "/ō/ open"): [("OW",)],
    ("i", "/ī/ open"): [("AY",)],
    ("i_e", "/ī/"): [("AY",)], ("a_e", "/ā/"): [("EY",)],
    ("o_e", "/ō/"): [("OW",)], ("u_e", "/ū/ /o͞o/"): [("UW",), ("Y", "UW")],
    ("e_e", "/ē/"): [("IY",)],
    ("j", "/j/"): [("JH",)], ("dge", "/j/"): [("JH",)],
    ("v", "/v/"): [("V",)], ("x", "/ks/"): [("K", "S")],
    ("old", "/ōld/"): [("OW", "L", "D")], ("ost", "/ōst/"): [("OW", "S", "T")],
    ("ind", "/īnd/"): [("AY", "N", "D")], ("ild", "/īld/"): [("AY", "L", "D")],
    ("ink", "/ink/"): [("IH", "NG", "K")], ("ank", "/ank/"): [("AE", "NG", "K")],
    ("ang", "/ang/"): [("AE", "NG")],
    ("a", "/ā/ open"): [("EY",)], ("u", "/ū/ open"): [("UW",), ("Y", "UW")],
    ("y", "/ī/ final"): [("AY",)], ("y", "/ē/ final"): [("IY",)],
    ("ee", "/ē/"): [("IY",)], ("ea", "/ē/ /ĕ/"): [("IY",), ("EH",)],
    ("ai", "/ā/"): [("EY",)], ("ay", "/ā/"): [("EY",)],
    ("oa", "/ō/"): [("OW",)], ("oo", "/o͞o/ /o͝o/"): [("UW",), ("UH",)],
    ("aw", "/aw/"): [("AO",)], ("au", "/aw/"): [("AO",)],
    ("all", "/awl/"): [("AO", "L")], ("al", "/awl/ /ahl/"): [("AO", "L"), ("AA", "L")],
    ("ie", "/ī/ /ē/"): [("AY",), ("IY",)], ("igh", "/ī/"): [("AY",)],
    ("ou", "/ow/ /o͞o/ /ŭ/"): [("AW",), ("UW",), ("AH",)],
    ("ow", "/ow/ /ō/"): [("AW",), ("OW",)],
    ("oi", "/oy/"): [("OY",)], ("oy", "/oy/"): [("OY",)],
    ("ew", "/o͞o/ /ū/"): [("UW",), ("Y", "UW")],
    ("ue", "/o͞o/ /ū/"): [("UW",), ("Y", "UW")],
    ("ar", "/ar/"): [("AA", "R")], ("or", "/or/"): [("AO", "R")],
    ("er", "/er/"): [("ER",)], ("ir", "/er/"): [("ER",)], ("ur", "/er/"): [("ER",)],
    ("ar", "/er/ unstressed"): [("ER",)], ("or", "/er/ unstressed"): [("ER",)],
    ("are", "/air/"): [("EH", "R")], ("air", "/air/"): [("EH", "R")],
    ("ear", "/air/ /eer/ /er/"): [("EH", "R"), ("IH", "R"), ("ER",)],
    ("ore", "/or/"): [("AO", "R")], ("eigh", "/ā/"): [("EY",)],
    ("ph", "/f/"): [("F",)], ("aught", "/awt/"): [("AO", "T")],
    ("oe", "/ō/"): [("OW",)], ("ey", "/ē/ /ā/"): [("IY",), ("EY",)],
    ("kn", "/n/"): [("N",)], ("wr", "/r/"): [("R",)], ("mb", "/m/"): [("M",)],
}

# Extra correspondences unlocked by gates rather than graphemes.
GATE_ARPA = {
    "magic-e": [("e", ())],                       # silent final e
    "soft-c": [("c", ("S",))],
    "soft-g": [("g", ("JH",))],
    "consonant-le": [("le", ("AH", "L"))],
    "schwa": [(v, ("AH",)) for v in "aeiou"],
    "suffix-ed": [("ed", ("T",)), ("ed", ("D",)), ("ed", ("IH", "D")),
                  ("ed", ("AH", "D"))],
    "suffix-es": [("es", ("IH", "Z")), ("es", ("AH", "Z")), ("es", ("Z",))],
    "suffix-er-est": [("est", ("AH", "S", "T")), ("est", ("IH", "S", "T"))],
}


def cmu_correspondences(cur):
    corr = []  # (lesson, spelling, phones)
    single = {}
    for l in cur.lessons:
        for g, p in l["graphemes"]:
            key = (g, p)
            if key not in ARPA:
                raise SystemExit(f"no ARPA mapping for grapheme {key} (L{l['n']})")
            spelling = g[0] if g.endswith("_e") else g
            for phones in ARPA[key]:
                corr.append((l["n"], spelling, phones))
                if len(spelling) == 1 and spelling not in "aeiou":
                    single.setdefault(spelling, (l["n"], phones))
        for gate in l["gates"]:
            for spelling, phones in GATE_ARPA.get(gate, []):
                corr.append((l["n"], spelling, phones))
            if gate == "two-syllable":
                # doubled middle consonants read as one sound
                for c, (n0, phones) in single.items():
                    corr.append((max(l["n"], n0), c + c, phones))
    return corr


def cmu_readable(word, prons, corr, heart_lessons):
    """Earliest lesson whose correspondences spell out a real pronunciation."""
    INF = 10_000
    best = heart_lessons.get(word, INF)
    for pron in prons.get(word, []):
        dp = [[INF] * (len(pron) + 1) for _ in range(len(word) + 1)]
        dp[0][0] = 0
        for i in range(len(word) + 1):
            for j in range(len(pron) + 1):
                if dp[i][j] == INF:
                    continue
                for lesson, g, phones in corr:
                    i2, j2 = i + len(g), j + len(phones)
                    if word[i:i2] == g and pron[j:j2] == tuple(phones):
                        dp[i2][j2] = min(dp[i2][j2], max(dp[i][j], lesson))
        best = min(best, dp[len(word)][len(pron)])
    return best if best < INF else None


def cmu_audit(cur):
    path = os.path.join(ROOT, "..", "..", "phonics-tool", "cmudict-0.7b.txt")
    words = [w for w in cur.ranks if w.isalpha()]
    needed = set(words)
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
    corr = cmu_correspondences(cur)
    heart_lessons = {}
    for l in cur.lessons:
        for w in l["heart"]:
            heart_lessons.setdefault(w.lower(), l["n"])
    agree = later = 0
    never, gap = [], []
    for w in words:
        spell, _ = cur.first_available(w)
        if spell is None:
            continue
        cmu = cmu_readable(w, prons, corr, heart_lessons)
        if cmu is None:
            never.append(w)
        elif cmu > spell + 5:
            gap.append((w, spell, cmu))
            later += 1
        else:
            agree += 1
    never.sort(key=lambda w: cur.ranks[w])
    gap.sort(key=lambda t: cur.ranks[t[0]])
    print(f"CMUdict audit over top-3000 (spelling-engine-readable words):")
    print(f"  agree (within 5 lessons): {agree}")
    print(f"  CMU much later: {later}")
    print(f"  CMU never aligns: {len(never)} — candidates for NOT_DECODABLE "
          f"or heart words")
    print("  top by rank, never:", ", ".join(never[:40]))
    print("  top by rank, much later:",
          ", ".join(f"{w}({s}->{c})" for w, s, c in gap[:20]))


if __name__ == "__main__":
    cur = load()
    if "--check" in sys.argv:
        check(cur)
    elif "--cmu" in sys.argv:
        cmu_audit(cur)
    else:
        build_html(cur)
