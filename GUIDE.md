# Bookroo Learn to Read — Curriculum Guide

This document is the source of truth for anyone (human or agent) writing or revising lessons.
Module 1 (lessons 1–10) is the canon: when in doubt, do what Module 1 does.

Related references:

- Lesson slide JSON: `lessons/lesson-N.json` (schema: `web/client/src/types/learn-to-read.ts`)
- Exercise catalog (every exercise, when it enters the curriculum): `EXERCISES.md`
- Full 9-module outline: `Learn to Read Module Order - Sheet1.csv`; coverage & ordering review: `MODULE_ORDER_REVIEW.md`
- Common Core alignment (trust artifact for schools): `STANDARDS_ALIGNMENT.md` / `.html`
- Decodable word lists & book pipeline: `phonics-tool/` (`lessons.json`, per-lesson `cumulative_words.csv`)
- Book writing guide: `phonics-tool/META_ANALYSIS.md`

---

## 1. The Program

**Mission:** take a child from zero to fluent reading, taught by a parent (the "reading helper") with **no preparation, no pre-knowledge, and no jargon**, in short 15–20 minute lessons, following the Science of Reading.

**Guiding principles**

1. Parent + child, together. The helper prompts, waits, corrects, celebrates — the child does the work.
2. No parent preparation. Every lesson is fully scripted; the helper just reads the screen.
3. Parent-friendly language. Kid-facing and helper-facing text never uses jargon ("sound," not "phoneme"). Educator terms may appear once, defined, in helper-only instructions.
4. Zero to fluent. Every module moves the child up this ladder:

   > hear sounds → see letters → map sounds↔letters → blend words → read for meaning → recognize words automatically → read sentences fluently

   Each activity trains exactly one rung. Lessons review lower rungs and push the highest rung the child has reached.

5. First exposure ≠ mastery. Concepts spiral across lessons; lessons are never pass/fail. Anti-frustration language is built in ("you can always repeat a lesson").
6. Practice leads to real reading. Isolated skill work pays off in an authentic decodable book in the same lesson.

**Module shape**

- A module is 8–10 lessons. Each lesson introduces exactly **one new thing**: one grapheme+sound, or one concept (heart words, ending in S). Lesson 1 is the only exception (M/A/T needed to make first words).
- Every module ends with a **review lesson** (no new content, all games + rereading the module's books) that ends with an explicit **readiness check** for the helper ("If {name} read most words with only light prompting, they're ready for Module N+1").
- One grapheme per lesson, ordered by the curriculum spec in `phonics-tool/lessons.json`. The ordering priorities: build readable words fast, high-frequency letters first, separate visually/aurally confusable letters.

---

## 2. The Lesson Grammar

Every standard lesson follows this skeleton (~18–25 slides, 15–20 min):

| #   | Segment                  | Slide types                                                                                                                                                             | Rules                                                                                                                                                                                                                      |
| --- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Welcome**              | `custom` ×1–2                                                                                                                                                           | Say what today holds ("one new letter and one new sound"). Warm, brief.                                                                                                                                                    |
| 2   | **Review**               | 2–4 of: `find-grapheme` (Eagle Eyes), `sound-to-grapheme`, `lost-sounds`, `identify-sound`, `card-stack`                                                                | Review BEFORE new learning. Short, active, diagnostic. Only previously-taught material may appear. Once a special case exists (heart words, -s words, Letter Friends) it joins the mixed review rotation.                  |
| 3   | **Teach the new thing**  | `grapheme-recall` (variant `new-letter`) → `grapheme-trace-air` → `grapheme-trace-palm` → `find-grapheme` → `introduce-sound` → `sound-pick-word-stack` (Elephant Ears) | Letter form before letter sound. Motor (trace) before visual search (find). Sound in isolation before sound-in-words.                                                                                                      |
| 4   | **Celebrate checkpoint** | `custom` + `confetti: true`                                                                                                                                             | "Amazing, you know N letters now!" Marks the pivot from learning to applying.                                                                                                                                              |
| 5   | **Apply: blend words**   | `finger-word` ×3–8                                                                                                                                                      | Finger Words with the new sound. Include the sticky-sound reasoning out loud. From lesson 5 on, mix in Imaginary Finger Words (concrete → mental). End each word by saying it plainly ("That's right, the word is 'mat'"). |
| 6   | **Check**                | `word-to-picture` / `picture-to-word`                                                                                                                                   | Meaning check — proves decoding produced comprehension, not just noise.                                                                                                                                                    |
| 7   | **Real reading**         | `books`                                                                                                                                                                 | The payoff. A decodable book using the cumulative set. The book reader ends with a built-in Comprehension Practice panel (2 questions per book).                                                                           |
| 8   | **Teach Tam**            | `teach-tam`                                                                                                                                                             | The child explains today's letter/sound/strategy to Tam. Metacognitive transfer; 1–2 minutes, helper gets suggested prompts.                                                                                               |
| 9   | **Conclusion**           | `conclusion` + confetti                                                                                                                                                 | Gems claimed here (2 per lesson) — this is what records completion.                                                                                                                                                        |

Variations are allowed inside segments (which review games, how many finger-words), but **don't drop segments** without a reason. Known intentional variants: review lessons (segment 2+7 only), heart-word lessons (segment 3 becomes the heart-word protocol, §4).

From Module 2 onward, two segments join the tail of the lesson (between Check and Books):

- **Brain Words** (`brain-words`): rapid reread of the growing list of already-decoded words to build automatic recognition. Decode first, recognize later — never the reverse.
- **Narrative Ninja** (`reading-fluency`): one sentence, three reads — (1) word-by-word (Finger Words allowed), (2) helper models with expression, (3) child reads with expression.

---

## 3. Hard Pedagogy Rules

These are never violated:

1. **Letter name ≠ sound.** Always "the letter M" vs "the /m/ sound." A word is read only after blending.
2. **Clean sounds.** Coach against added vowels ("TUH", "TIH"); stop sounds are crisp and short. Helper instructions carry the correction script.
3. **Vowel display convention.** Vowel sounds show helper letters (e.g. /a/ as in "bag") — the extra letters indicate pronunciation and are never read aloud. Explain this the first time only.
4. **Concrete → mental.** Physical fingers → finger pairs → knuckle blending → Imaginary Finger Words. Never start abstract.
5. **Decodability is absolute.** Every word the child is asked to read must be fully decodable from the cumulative taught set (check `phonics-tool` cumulative lists) — or be an explicitly-taught heart word. No exceptions, including game distractors, book kid-lines, and example words.
6. **Games are practice wrappers, not decoration.** Each named game tests one precise mapping (see §5). Don't invent a new game when an existing one covers the mechanic.
7. **The child does the work.** Helper prompts, waits ("Wait — then provide feedback"), then reveals. Answers are revealed, never just told.
8. **Decoding ≠ comprehension.** Any word the child may not know gets a one-line kid-friendly gloss immediately after decoding it ("To lug something means to carry something big and heavy").

---

## 4. Special-Case Protocols (Module 2+)

Module 1 assumes one letter = one sound = decodable words. Each departure from that gets an explicit, named, kid-facing protocol:

- **Heart Words** (sight words: I, a, the, …). Label them honestly: "this word doesn't follow the rules we've learned so far, so we learn it by heart." Introduce a few at a time, then immediately read them inside sentences (`story-words`: helper reads sentence → child finds the word → child reads the sentence). They join Brain Words and mixed review forever after.
- **Letter Friends** (digraphs: sh, ch/tch, ck, qu). Two letters that hold hands and make one sound. When decoding, the child looks for Letter Friends **first**, then Sticky Sounds. Trace both letters at introduction. Sub-cases matter: ch is truly one new sound; ck is a second spelling of /k/ (one sound, two letters — not two /k/s); qu is an inseparable pair (Q never appears without U).
- **Flexible sounds** (final S = /s/ or /z/, the word "a" = /A/ or /uh/). Teach the child a _strategy_, not a rule: try the likely sound → listen — is it a real word? → if not, flip. The linguistic rule (voiced/unvoiced neighbors) goes in helper-only instructions, if anywhere.
- **Morphology** (-s endings, later -ed, -ing). Taught as a meaning pattern ("S at the end can mean more than one"), not as a new sound.
- **Word Chains** (`word-chain`: RAN → RAM → RAMP → CAMP). Change exactly one grapheme per link; the child reads every link. Builds orthographic mapping through minimal contrast.
- **Sentences before fluency.** Word accuracy → phrase reading → sentence reading with expression (Narrative Ninja). Sentences use only decodable + taught heart words.

---

## 5. Canon Vocabulary

Kid-facing names are part of the product. Use them exactly, bolded (`**Finger Words**`), and never rename an existing one:

| Name                       | What it is                                                                                                                                                  |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Finger Words**           | The blending strategy: assign letters to fingers, say each sound, blend along the knuckles with no gaps, repeat faster until the word appears.              |
| **Imaginary Finger Words** | The same strategy performed entirely mentally (from lesson 5).                                                                                              |
| **Sticky Sounds**          | Stop consonants (t, p, d, b, g, c…) that can't be held alone; they stick to the sound after them. Finger pairs touch.                                       |
| **Letter Friends**         | Digraphs — two letters, one sound (plural: "Letter Friends", always).                                                                                       |
| **Heart Words**            | Words learned by heart because they don't (yet) follow the rules.                                                                                           |
| **Brain Words**            | Words the child has decoded enough times to recognize instantly.                                                                                            |
| **Elephant Ears**          | Hear a spoken word, thumbs up/down if it contains the target sound (`sound-pick-word-stack`).                                                               |
| **Eagle Eyes**             | Find the target letter among distractors (`find-grapheme`).                                                                                                 |
| **Lost Sounds**            | The letters lost their sounds — the child gives each one back (`lost-sounds`).                                                                              |
| **Narrative Ninja**        | Repeated-reading fluency routine (`reading-fluency`).                                                                                                       |
| **Teach Tam**              | The child teaches today's concept to Tam.                                                                                                                   |
| Reading friends            | Tam (brown yak), Sam (creme chicken), Pam (purple rhino), Jim (blue rhino), Bob (gray bear), Lulu (red lobster). Character names double as decodable words. |
| **Rhyme Time**             | Hear a word, pick the picture that rhymes (`rhyme-match`).                                                                                                  |
| **Switcheroo**             | Two pictures; tap the letter that must change to spell the new word (`letter-swap`).                                                                        |
| **Word Builder**           | Build the word from a letter bank after seeing its picture (`word-builder`, mode `full`).                                                                   |
| **Letter Boxes**           | Fill the one missing letter in the word (`word-builder`, mode `missing`).                                                                                   |
| **Picture Quest**          | Read the word, find its picture — or the reverse (`word-to-picture` / `picture-to-word`).                                                                   |
| **Sound Swap**             | Oral: change one sound in a word to make a new word (planned).                                                                                              |

The full catalog — including when each exercise enters the curriculum — is `EXERCISES.md`. Public directory: `/courses/learn-to-read/exercises`.

---

## 6. Voice & Writing Rules

Slides speak through two channels:

- **Verbal** (blue) — the helper reads it aloud, word for word. Write for the child's ear: short sentences, warm, playful, direct questions.
- **Instruction** (brown) — helper-only. Technique, pacing, what to do if the child struggles, why this matters. This is where "wait time," articulation corrections, and any adult-level explanation live.

Rules:

- `{name}` templating personalizes both channels.
- Encouragement is frequent but specific ("You know 4 letters now!"), with confetti at real milestones only (checkpoint + conclusion).
- Every new mechanic gets a one-time explanation slide (and a video if it's physical, like Finger Words); afterwards it's referenced by name with a one-line reminder ("As a reminder…").
- Never pressure mastery: recap slides remind the helper the concept will spiral.
- Books slides invite conversation ("Feel free to talk about the illustrations and the story").

---

## 7. Words & Books

- Word selection: prefer high-frequency words from the CPB lexicon (`phonics-tool` generates `new_words.csv` / `cumulative_words.csv` per lesson). Never teach an obscure word just because it's decodable.
- Decodable books: kid-read text is all-caps, strictly limited to the cumulative set + taught heart words. Adult-read (blue) text carries narration and richer vocabulary. 9–12 spreads; a refrain that repeats ~3 times, then a twist; final spread is the punchline. Full craft guide: `phonics-tool/META_ANALYSIS.md`.
- Every grapheme lesson should ship with its own decodable book that features the new sound. A lesson without a book is an unfinished lesson.
- "Blue words" inside books (words beyond the child's set) are read by the helper — the lesson explains this convention when it first appears.

---

## 8. Platform Notes (what the software can do)

- Slide schema: `web/client/src/types/learn-to-read.ts`. All slides support `pre`/`post` text blocks (`value`/`prepend`/`append`/`replace`/`insert_after`), `confetti`, `label`, `randomize`.
- **Autograded** (client-side tap-to-answer with correct/incorrect feedback): `find-grapheme`, `sound-to-grapheme`, `sound-pick-word-stack`, `sound-in-word`, `sound-at-position`/`sound-train`, `word-to-picture`, `picture-to-word`, `word-grid`/`picture-grid`, partially `card-stack`. Where autograding is optional it defaults **off** — the helper can simply accept the child's spoken answer; tapping each answer is slower.
- **Helper-graded** (no way to autograde speech): `finger-word`, `brain-words`, `reading-fluency`, `lost-sounds`, card flashes, tracing.
- Nothing per-slide is persisted. Completion is binary (gems claimed on the conclusion slide). Keep this in mind before designing anything adaptive (§9).
- Autogradable mechanics can also ship as standalone games at `/reading-games` (Eagle Eyes, Letter Setter, Letter Boxes) for practice and future classroom use.
- Authoring: live JSON editor + preview at `/courses/learn-to-read/editor`. Printables (tracing, flash cards, coloring) at `/courses/learn-to-read/printables`.

---

## 9. QA Checklist (run on every lesson before shipping)

Derived from real bugs found in drafts:

1. **Phonics-rule consistency.** When a slide contrasts two sounds (final S /s/ vs /z/), the stated rule and the stated answer must agree. (Real bug, since fixed: lesson 11 TOPS said "S makes /s/ after P, so start with /z/." Lesson 11 now teaches final S via the Buzz Check — buzzy vs. not-buzzy sounds — instead of per-letter cues.)
2. **Right letters in explanations.** (Real bug: lesson 21 CHIPS says "letter friends when **S** is right before H" — should be C.)
3. **Decodability audit.** Every kid-read word (practice, distractors, sentences, book text) passes the cumulative-set check for that lesson number.
4. **Review only covers taught material.** (Real bug: SH appears in lost-sounds reviews from lesson 21 on, but SH's lesson doesn't exist yet.)
5. **Terminology exact and consistent.** "Letter Friends" (plural), bolded canon names, letter-vs-sound phrasing correct everywhere.
6. **Structure complete.** Welcome, review, one new thing, checkpoint confetti, blending, check, book (real ID, not placeholder), Teach Tam (or module-appropriate equivalent), conclusion.
7. **Channel correctness.** Nothing meant for the helper's eyes only is in a verbal block, and vice versa. Jargon only in instruction blocks, defined.
8. **{name} templating** present in personalized lines; no hardcoded child names.
9. **Distractor sanity.** Choice sets use taught letters; visually confusable pairs (b/d, m/n) appear deliberately, not accidentally, and not in the same set the week a letter is introduced.
10. **Book present and correct** for the lesson's cumulative set; blue-word convention respected.

---

## 10. Open Threads (decided direction, not yet built)

- **Missing lessons 19 and 20** — 19 is the Module 2 review lesson, 20 is SH (Module 3's first lesson; later reviews already reference SH). Must exist before lesson 21 ships. Full module map and ordering review: `MODULE_ORDER_REVIEW.md`.
- **Module 0 (pre-reading)**: for kids who find lesson 1 hard — oral-only phonological awareness (rhyming, syllable clapping, first-sound games, Elephant Ears without letters). Recommend, don't require.
- **Encoding/spelling**: ✅ built July 2026 — the `word-builder` slide type ("Word Builder" full-build mode, "Letter Boxes" missing-letter mode) plus reading-game versions. Schedule into lessons per `EXERCISES.md` (Letter Boxes from L8, Word Builder from L12).
- **Jump Ahead placement**: a short placement experience (built from module review lessons) that tells a parent which lesson to start at — for kids who already know some letters.
- **Standards alignment doc**: ✅ shipped July 2026 — `STANDARDS_ALIGNMENT.md`/`.html` plus the public page `/courses/learn-to-read/common-core` (data: `client/src/data/learn-to-read-standards.ts`). Update coverage badges as modules ship; a PDF export for school buyers is the remaining nice-to-have.
- **Lowercase letters**: promised "starting in Lesson 30" (lesson 1). The plan for teaching them needs to exist before then.
- **Adaptivity**: lessons are static and linear; nothing per-slide is tracked. The pragmatic path, in order:
  1. **Helper-choice branching (no new infra):** instruction blocks that say "If {name} found this tricky, repeat X / if easy, skip ahead" — static slides, human router. Cheap, aligned with the parent+child principle.
  2. **Persist per-slide results:** autograded slides already compute correct/incorrect client-side; start posting them with lesson completion. No behavior change, just data.
  3. **Dynamic review only:** keep teaching slides hand-authored and static; generate the _review segments_ (and review-day lessons) from the child's miss history. Review is where personalization pays off and where wrong generation does the least harm.
     Full adaptive lesson branching is not worth it until (2) has produced real data.
