# Module Order Review — Coverage & Sequencing

A review of `Learn to Read Module Order - Sheet1.csv` (the 90-lesson, 9-module outline) against
the Module 1–3 drafts, the Science of Reading, and the program's own principles (see `GUIDE.md`).
Recommendations are proposals with rationale — priorities marked ★★★ (must fix) / ★★ (high value) / ★ (polish).

## 0. Numbering map (resolved)

The sheet and the live site share one numbering; local `lessons/lesson-N.json` files differ by
the Module 1 review lesson you inserted, and the sheet's own skip of lesson 18 heals the offset:

| Sheet / live | Local files |
|---|---|
| 1–9 (Module 1: m,a,t,s,p,i,n,d,o,b,g) | 1–9, **+10 = Module 1 Review (local addition — add it to the sheet)** |
| 10–17 (Module 2: ending-s, e, h, heart words, l, c, u, r) | 11–18 |
| 18 (unused in sheet) | — |
| 19 (Module 2 Review) | **19 — missing file, to be written** |
| 20 (SH, first Module 3 lesson) | **20 — missing file, to be written** |
| 21+ | 21+ (aligned from here on) |

So: local 19 = Module 2 Review, local 20 = SH, and local 21–25 are Module 3 drafts.
Module 3 still needs 26 (f), 27 (ss/ll/zz/ff), 28 (th voiced), 29 (Review).

Housekeeping: the sheet's columns C–F look like a stale parallel ordering (e.g. j and w are on
swapped rows vs. column B) — worth deleting or labeling so they don't mislead future authors.
"Sound Detective" (lesson 1 concepts column) doesn't exist in lesson-1.json — presumably renamed
to Elephant Ears; update the sheet.

## 1. Coverage gaps — sounds/patterns never taught anywhere in the 90 lessons

★★★ **/aw/ spellings: aw, au (+ al/all)** — saw, draw, because, caught, ball, all, call, talk.
Very high frequency; completely absent. Even with a cot-caught-merger accent, the *graphemes*
aw/au/al must be taught ("another way to spell /o/"). Best home: Module 6 (replace `ei`, see §2).

★★★ **Soft c and soft g** — ice, face, nice, race, place; age, page, cage, huge. Needed almost
immediately once a_e arrives (lesson 32), or those words misdecode. Best home: Module 4–5.

★★★ **Consonant-le** — little, apple, table, purple. The dominant second-syllable pattern; must
land with two-syllable work in Module 5.

★★ **-ed suffix (3 sounds: /d/ jumped→/t/, played→/d/, landed→/ed/)** and **-ing** — the outline
teaches ending-s morphology in Module 2 and then no morphology ever again. -ed fits Module 4;
-ing pairs naturally with ng (lesson 43).

★★ **Schwa** — unavoidable once two-syllable words start (Module 5): about, banana, wagon. Teach
as a strategy, not a rule ("in longer words some vowels get lazy and say /uh/ — if the word
sounds almost right, try the lazy sound"), consistent with the flexible-sounds protocol.

★★ **Contractions** — can't, it's, I'm, don't, let's. Books will want them; a single lesson +
mixed review coverage, Module 5–6.

★ **Compound words** — sunset, hotdog, laptop. Cheap, delightful bridge into two-syllable
reading ("two words you already know, stuck together"); first slide of Module 5's syllable work.

★ **dge** (bridge, badge) — sibling of tch; Module 7+.

★ Consciously deferred (list them somewhere so they read as decisions, not oversights):
silent letters kn/wr/mb, /zh/ (measure), air/ear/ore, tion/sion, prefixes/suffixes beyond the
above. Candidates for a Module 10 / "advanced patterns" if zero-to-fluent needs them.

**Heart words** ★★ — the outline schedules was/what/want (31), hi/by/why (34), to/do (36),
are (72), maybe you (22). That's far short of what decodable-ish books need: said, of, have,
come, some, one, they, were, there, where, who, your, put, could/would/should… Recommend a
standing heart-word track: 2–3 per review lesson + as needed per book, recorded in
`phonics-tool/lessons.json` so the decodability checker stays truthful. (Note: hi/by/why at 34
aren't really heart words — they're y-as-long-i, formally taught at 85. Either teach y=/ī/ at 34
or accept the temporary heart-word framing and reconcile at 85.)

## 2. Ordering issues

★★★ **Blends are taught 3 modules after kids already read them.** The Module 2–3 drafts use
BEST, TENT, HAND, CAMP, MUST (final blends) and BLACK, SKIP, CLICK, SQUID (initial blends);
Module 3's concept is literally "5 letter words." Yet bl/cl (46), fl/gl (48), br/dr (49), sm/st
(56), pr/vr (58), gr/tr (61), sp/sn (63), pl/sl (65), cr/fr (67), sw/tw (69), str (71), spl (73),
spr (75), thr (77) occupy **14 lessons across Modules 5–8**. Blends aren't new sounds — they're
adjacent known sounds, and Finger Words already handles them (one finger per sound). Recommend:
teach "blending neighbors" once as a skill inside Module 3 when 5-letter words begin, and
repurpose the 14 slots for the §1 gaps plus fluency/volume lessons (§3). If you keep any blend
lessons, keep them as light *practice* lessons, not new-concept lessons. (Also: "/vr/" at
lesson 58 is almost certainly a typo — no common English words start with vr.)

★★★ **Silent-e is five scattered lessons with no unifying concept.** a_e (32), i_e (34), o_e
(36), u_e (38) in Module 4… then e_e (45) orphaned in Module 5. Give it a kid-facing name
(the program's move for every pattern: Sticky Sounds, Letter Friends, Heart Words — e.g.
"Magic E" / "Bossy E", name TBD → add to GUIDE §5 canon), teach the concept once at 32, then
each vowel becomes a quick variation. Pull e_e into Module 4 with its siblings.

★★ **ay is taught twice** — lesson 32 ("ay and a_e") and lesson 81 ("ay (play)"). Recommend:
32 teaches a_e only (keeps the Magic E concept clean); ay moves to the vowel-team modules —
and given day/play/say/way frequency, it belongs in Module 6, not Module 9.

★★ **Lowercase at lessons 41–42 contradicts shipped copy and is late.** Lesson 1 promises
"starting in Lesson 30, we'll also include lowercase letters"; the sheet says 41–42. Beyond the
inconsistency: real books are ~95% lowercase, and two lessons for 26 new letterforms is thin.
Recommend gradual exposure (show both forms from Module 3–4 in grapheme slides and Eagle Eyes
variants; printables already support lowercase tracing) with 41–42 as consolidation — then fix
the lesson-1 text either way.

★★ **Modules 6–9 are phonics-only; the concepts column goes empty.** "Zero to fluent" means the
back half must shift weight from new graphemes to connected-text volume: an end-of-lesson
passage every lesson, Narrative Ninja continuing throughout, periodic "just read" lessons
(the freed blend slots), and longer decodable books. Otherwise the program teaches 90 patterns
but never builds mileage.

★ **ei (ceiling) at 55** is rare (ceiling/receive/either) — weak use of a Module 6 slot next to
missing aw/au. Defer ei to Module 9 with the other alternate spellings (it fits the 81–90 theme).

★ **ough (89)** is the most multi-valued grapheme in English (though/through/tough/cough). If it
stays, it should explicitly lean on the try-and-listen flexible-sounds strategy; teaching it as
"ough says /ō/" will backfire.

★ **Module 9 has no review/finale.** Add lesson 91: cumulative review + a celebratory
"graduation" readiness check, mirroring every other module's close.

★ Fine as designed (endorsed): th voiced (28) before unvoiced (39) — the/this/that frequency
justifies it; ie and oo and ow and y each taught twice with different sounds — consistent with
the flexible-sounds protocol; "you" as a heart word at 22 — yes, phonics-tool already models it;
one flagship spelling per long vowel in Module 4 before alternates in 6/9 — textbook-correct.
Minor: lesson 36's example list "home, boat, no" mixes o_e with oa (54) and open syllables —
tidy the sheet.

## 3. What each module needs beyond phonics (concept track)

The concepts column currently stops at Module 5. Proposed continuation, one new *named* concept
per module (matching the canon-vocabulary pattern):

| Module | Existing concepts | Add |
|---|---|---|
| 3 | 5-letter words | "blending neighbors" (blends as skill, not sounds) |
| 4 | — | **Magic E** (name TBD); -ed suffix; soft c |
| 5 | 6-letter words, two syllables, clapping | compound words; consonant-le; schwa-as-strategy; soft g; -ing; lowercase consolidation |
| 6 | — | **Vowel Teams** (name TBD); aw/au; ay; contractions |
| 7 | — | reading mileage: passages + "just read" lessons; dge |
| 8 | — | **Bossy R** (name TBD) unifying ar/or/er/ir/ur (er=ir=ur is one sound, three spellings) |
| 9 | — | "one sound, many spellings" review lens; ei; graduation review (91) |

Each new named concept should be added to `GUIDE.md` §5 when christened.

## 4. Scale flags (not curriculum, but plan-breaking if ignored)

- **Books:** GUIDE says every grapheme lesson ships with a decodable book → ~75 books for 90
  lessons. If that's not feasible, decide the fallback now (book every 2–3 lessons in Modules
  6–9, or reread-with-new-eyes assignments) so lesson drafts don't stall on missing books.
- **Read-alone vs read-together:** the outline never marks when books shift from
  parent-supported to independent. Natural milestone: Module 4–5 (silent-e + 6-letter words).
  Worth a column in the sheet.
- **Module 0** (pre-reading, oral-only phonological awareness) remains an open thread in
  GUIDE §10 — nothing in this outline blocks it; lesson-1's Elephant Ears/rhyming mechanics
  are the seed.

## 5. Decision list (for Kesler)

1. Consolidate the 14 blend lessons → free slots for aw/au, soft c/g, -le, -ed/-ing, schwa,
   contractions, fluency mileage? (My recommendation: yes.)
2. Lowercase: gradual from Module 3–4 with 41–42 as consolidation, or keep the hard cut at 41?
   (Either way, reconcile the "Lesson 30" promise in lesson-1.json.)
3. Kid-facing names for Magic E / Vowel Teams / Bossy R (canon additions).
4. Heart-word track: adopt the 2–3-per-review cadence and pick the early list (said, have,
   they, of, come, some, were, there…)?
5. Books cadence for Modules 6–9.
6. ay to Module 6 and ei to Module 9?
