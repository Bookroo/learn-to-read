#!/usr/bin/env python3
"""Extract the machine-readable curriculum from MODULE_ORDER_PROPOSED.html.

DEPRECATED as the normal workflow: data/curriculum.json is now the source of
truth — edit it directly and regenerate the doc with
scripts/build-module-order.py. Keep this script only as a recovery tool in
case the HTML is ever hand-edited again (re-run it to pull the edits back
into curriculum.json; authored graphemes/gates merge in from CODE below).

Usage: python3 scripts/extract-curriculum.py
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "MODULE_ORDER_PROPOSED.html")


def slugify(title):
    s = title.lower()
    s = s.replace("&amp;", "and").replace("&", "and").replace("→", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


# ---------------------------------------------------------------------------
# Authored code: what each lesson unlocks, keyed by slug.
#   g: graphemes as [spelling, phoneme] pairs
#   gates: named engine abilities this lesson unlocks (see availability.py)
# Reviews / fluency / graduation lessons unlock nothing and may be omitted.
# ---------------------------------------------------------------------------
CODE = {
    "m-t-a": {"g": [["m", "/m/"], ["t", "/t/"], ["a", "/ă/"]]},
    "s": {"g": [["s", "/s/"]]},
    "p": {"g": [["p", "/p/"]]},
    "i": {"g": [["i", "/ĭ/"]]},
    "n": {"g": [["n", "/n/"]]},
    "d": {"g": [["d", "/d/"]]},
    "o": {"g": [["o", "/ŏ/"]]},
    "b": {"g": [["b", "/b/"]]},
    "g": {"g": [["g", "/g/"]]},
    "ending-in-s": {"g": [["s", "/z/"]], "gates": ["suffix-s"]},
    "e": {"g": [["e", "/ĕ/"]]},
    "h": {"g": [["h", "/h/"]]},
    "heart-words": {},
    "l": {"g": [["l", "/l/"]]},
    "c": {"g": [["c", "/k/"]]},
    "u": {"g": [["u", "/ŭ/"]]},
    "r": {"g": [["r", "/r/"]]},
    "z": {"g": [["z", "/z/"]]},
    "sh": {"g": [["sh", "/sh/"]]},
    "ch-tch": {"g": [["ch", "/ch/"], ["tch", "/ch/"]]},
    "y": {"g": [["y", "/y/"]]},
    "k-ck": {"g": [["k", "/k/"], ["ck", "/k/"]]},
    "qu": {"g": [["qu", "/kw/"]]},
    "f": {"g": [["f", "/f/"]]},
    "ff-ll-ss-zz": {"g": [["ff", "/f/"], ["ll", "/l/"], ["ss", "/s/"], ["zz", "/z/"]]},
    "th-both-sounds": {"g": [["th", "/th/ /t͟h/"]]},
    "w-wh": {"g": [["w", "/w/"], ["wh", "/w/"]]},
    "ng-and-nk": {"g": [["ung", "/ŭng/"], ["ong", "/ŏng/"], ["unk", "/ŭnk/"], ["onk", "/ŏnk/"], ["ng", "/ng/"], ["nk", "/nk/"]]},
    "ing": {"g": [["ing", "/ing/"]], "gates": ["suffix-ing"]},
    "meet-the-vowels": {"g": [["e", "/ē/ open"], ["o", "/ō/ open"], ["i", "/ī/ open"]], "gates": ["open-final"]},
    "magic-e-i-e": {"g": [["i_e", "/ī/"]], "gates": ["magic-e"]},
    "j-dge": {"g": [["j", "/j/"], ["dge", "/j/"]]},
    "a-e": {"g": [["a_e", "/ā/"]]},
    "v": {"g": [["v", "/v/"]]},
    "o-e": {"g": [["o_e", "/ō/"]]},
    "x": {"g": [["x", "/ks/"]]},
    "u-e": {"g": [["u_e", "/ū/ /o͞o/"]]},
    "e-e": {"g": [["e_e", "/ē/"]]},
    "old-and-ost": {"g": [["old", "/ōld/"], ["ost", "/ōst/"]]},
    "ind-and-ild": {"g": [["ind", "/īnd/"], ["ild", "/īld/"]]},
    "lowercase-letters": {},
    "ink-and-ing": {"g": [["ink", "/ink/"]]},
    "ank-and-ang": {"g": [["ank", "/ank/"], ["ang", "/ang/"]]},
    "soft-c": {"gates": ["soft-c"]},
    "soft-g": {"gates": ["soft-g"]},
    "reading-two-syllable-words": {"gates": ["two-syllable"]},
    "es-endings": {"gates": ["suffix-es"]},
    "consonant-le": {"gates": ["consonant-le"]},
    "ed-endings": {"gates": ["suffix-ed"]},
    "endings-that-change-the-base": {"gates": ["doubling", "drop-e"]},
    "open-chunks": {"g": [["a", "/ā/ open"], ["u", "/ū/ open"]], "gates": ["open-internal", "schwa"]},
    "vowel-y": {"g": [["y", "/ī/ final"], ["y", "/ē/ final"]], "gates": ["vowel-y"]},
    "vowel-teams-ee": {"g": [["ee", "/ē/"]]},
    "ea": {"g": [["ea", "/ē/ /ĕ/"]]},
    "ai": {"g": [["ai", "/ā/"]]},
    "ay": {"g": [["ay", "/ā/"]]},
    "oa": {"g": [["oa", "/ō/"]]},
    "oo-both-sounds": {"g": [["oo", "/o͞o/ /o͝o/"]]},
    "aw": {"g": [["aw", "/aw/"]]},
    "au": {"g": [["au", "/aw/"]]},
    "all-and-al": {"g": [["all", "/awl/"], ["al", "/awl/ /ahl/"]]},
    "ie-both-sounds": {"g": [["ie", "/ī/ /ē/"]]},
    "igh": {"g": [["igh", "/ī/"]]},
    "ou-four-sounds": {"g": [["ou", "/ow/ /o͞o/ /ŭ/"]]},
    "ow-both-sounds": {"g": [["ow", "/ow/ /ō/"]]},
    "oi": {"g": [["oi", "/oy/"]]},
    "oy": {"g": [["oy", "/oy/"]]},
    "ew": {"g": [["ew", "/o͞o/ /ū/"]]},
    "ue": {"g": [["ue", "/o͞o/ /ū/"]]},
    "contractions": {"gates": ["contractions"]},
    "bossy-r-ar": {"g": [["ar", "/ar/"]]},
    "or": {"g": [["or", "/or/"]]},
    "er": {"g": [["er", "/er/"]]},
    "ir": {"g": [["ir", "/er/"]]},
    "ur": {"g": [["ur", "/er/"]]},
    "ar-and-or-can-say-er": {"g": [["ar", "/er/ unstressed"], ["or", "/er/ unstressed"]]},
    "are": {"g": [["are", "/air/"]]},
    "air": {"g": [["air", "/air/"]]},
    "ear-four-sounds": {"g": [["ear", "/air/ /eer/ /er/"]]},
    "ore": {"g": [["ore", "/or/"]]},
    "er-and-est": {"gates": ["suffix-er-est"]},
    "eigh": {"g": [["eigh", "/ā/"]]},
    "ph": {"g": [["ph", "/f/"]]},
    "aught": {"g": [["aught", "/awt/"]]},
    "ough": {},
    "oe": {"g": [["oe", "/ō/"]]},
    "ey-both-sounds": {"g": [["ey", "/ē/ /ā/"]]},
    "kn": {"g": [["kn", "/n/"]]},
    "wr": {"g": [["wr", "/r/"]]},
    "mb": {"g": [["mb", "/m/"]]},
    "three-syllable-words": {"gates": ["three-syllable"]},
}


def parse():
    html = open(DOC).read()
    lessons = []
    module = None
    module_title = None
    # Walk the document in order, tracking module headers and lesson rows.
    pattern = re.compile(
        r'<h2>Module (\d+) — (.*?)</h2>'
        r'|<td class="num">(\d+)</td>\s*<td class="what">\s*(.*?)</td>\s*'
        r'<td>(.*?)</td>\s*<td class="detail">(.*?)</td>\s*'
        r'<td class="examples">(.*?)</td>',
        re.S,
    )
    for m in pattern.finditer(html):
        if m.group(1):
            module = int(m.group(1))
            module_title = clean(m.group(2))
            continue
        num = int(m.group(3))
        what = m.group(4)
        sub_m = re.search(r'<span class="sub"\s*>(.*?)</span\s*>', what, re.S)
        title = clean(re.sub(r'<span class="sub"\s*>.*?</span\s*>', '', what, flags=re.S))
        tags = re.findall(r'class="tag t-(\w+)">', m.group(5))
        detail_html = m.group(6)
        intros = re.findall(
            r'intro-(concept|exercise)"\s*>(.*?)</span', detail_html, re.S)
        detail = clean(re.sub(r'<div class="detail-intros">.*?</div>', '',
                              detail_html, flags=re.S))
        ex_html = m.group(7)
        # Flatten nested dolch spans so the outer .words spans match cleanly
        # (dolch marking is re-derived from the dolch_pre_k list on render).
        ex_flat = re.sub(r'<span class="dolch-word"\s*>(.*?)</span\s*>', r'\1',
                         ex_html, flags=re.S)
        examples, heart = [], []
        for span in re.findall(r'<span class="words"\s*>(.*?)</span\s*>', ex_flat, re.S):
            is_heart = 'heart words:' in span
            text = clean(re.sub(r'<b class="example-label"\s*>.*?</b\s*>', '', span, flags=re.S))
            if is_heart:
                heart.extend(w.strip() for w in re.split(r'[;,]', text) if w.strip())
            elif text:
                examples.append(text)  # group string, commas/semicolons kept
        lessons.append({
            "n": num,
            "slug": slugify(title),
            "title": title,
            "sub": clean(sub_m.group(1)) if sub_m else "",
            "module": module,
            "module_title": module_title,
            "tags": tags,
            "detail": detail,
            "intros": [{"kind": k, "name": clean(v)} for k, v in intros],
            "examples": examples,
            "heart": heart,
        })
    return lessons


def clean(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace('&amp;', '&').replace('&nbsp;', ' ')
    return re.sub(r'\s+', ' ', s).strip()


DOLCH_PRE_K = [
    "a", "and", "away", "big", "blue", "can", "come", "down", "find", "for",
    "funny", "go", "help", "here", "i", "in", "is", "it", "jump", "little",
    "look", "make", "me", "my", "not", "one", "play", "red", "run", "said",
    "see", "the", "three", "to", "two", "up", "we", "where", "yellow", "you",
]


def parse_extras(html, lessons):
    slug_by_num = {l["n"]: l["slug"] for l in lessons}
    extras = {}
    extras["rules"] = [
        {"title": clean(t).rstrip("."), "text": clean(s)}
        for t, s in re.findall(
            r'<li><b>(.*?)</b\s*>\s*(.*?)</li>', html, re.S)
    ]
    extras["modules"] = [
        {"n": int(n), "title": clean(t), "theme": clean(theme)}
        for n, t, theme in re.findall(
            r'<h2>Module (\d+) — (.*?)</h2>\s*</div>\s*'
            r'<p class="module-theme">\s*(.*?)</p>', html, re.S)
    ]
    reference = []
    for kind, name, num, how in re.findall(
            r'<span class="reference-label reference-(concept|exercise)"\s*'
            r'>(.*?)</span\s*>\s*</td>\s*<td>Lesson (\d+)</td>\s*<td>\s*(.*?)\s*</td>',
            html, re.S):
        reference.append({"kind": kind, "name": clean(name), "how": clean(how)})
    extras["reference"] = reference
    m = re.search(
        r'<div class="note">\s*<strong\s*>(.*?)</strong\s*>(.*?)</div>\s*'
        r'<p>\s*(.*?)\s*</p>', html, re.S)
    extras["contractions"] = {
        "rule_strong": re.sub(r'Before Lesson \d+', 'Before Lesson {n}',
                              clean(m.group(1))),
        "rule_text": clean(m.group(2)),
        "phrases_html": re.sub(r'\s+', ' ', m.group(3)).strip(),
    }
    leftover = []
    sect = html[html.index("Leftover Top-500 Words"):]
    sect = sect[:sect.index("</table>")]
    for word, rank, sug in re.findall(
            r'<td><i>(.*?)</i></td>\s*<td>(\d+)</td>\s*<td>(.*?)</td>', sect, re.S):
        sug = clean(sug)
        lm = re.match(r'Lesson (\d+) — (.*)$', sug)
        if lm:
            entry = {"word": clean(word), "rank": int(rank),
                     "slug": slug_by_num[int(lm.group(1))], "note": lm.group(2)}
        else:
            entry = {"word": clean(word), "rank": int(rank), "note": sug}
        leftover.append(entry)
    extras["leftover"] = leftover
    extras["dolch_pre_k"] = DOLCH_PRE_K
    return extras


def main():
    lessons = parse()
    assert [l["n"] for l in lessons] == list(range(1, len(lessons) + 1)), \
        "lesson numbers are not sequential"
    unmatched = set(CODE) - {l["slug"] for l in lessons}
    assert not unmatched, f"CODE slugs not found in doc: {unmatched}"
    for l in lessons:
        code = CODE.get(l["slug"], {})
        l["graphemes"] = code.get("g", [])
        l["gates"] = code.get("gates", [])
    data = {"lessons": lessons}
    data.update(parse_extras(open(DOC).read(), lessons))
    out = os.path.join(ROOT, "data", "curriculum.json")
    with open(out, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    n_code = sum(1 for l in lessons if l["graphemes"] or l["gates"])
    print(f"{len(lessons)} lessons ({n_code} with code), "
          f"{len(data['reference'])} reference rows, "
          f"{len(data['leftover'])} leftover rows -> {out}")


if __name__ == "__main__":
    main()
