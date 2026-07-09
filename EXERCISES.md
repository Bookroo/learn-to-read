# Exercise Catalog — Learn to Read

The master list of every exercise and practice mechanic in the program: what it trains, where it
lives (lesson slides and/or `/reading-games`), how it's graded, and the lesson where it enters the
curriculum. When writing lessons, pick from this list — don't invent a new mechanic when an
existing one covers the skill (GUIDE §3.6).

Lesson numbers use **local file numbering** (see MODULE_ORDER_REVIEW §0).

Two tiers, per program philosophy:
- **Core** — scheduled into lessons at a specific point and part of the review rotation.
- **Extra practice** — always available as a practice tool (reading game / printable) for kids who
  need more repetition of a fundamental; never required to progress.

Public-facing directory of these exercises: `/courses/learn-to-read/exercises`.

---

## 1. Hear sounds (phonological & phonemic awareness)

| Exercise | Mechanic | Grading | Slide type | Reading game | Introduce | Tier |
|---|---|---|---|---|---|---|
| **Elephant Ears** | Helper says a word; child thumbs up/down if it has the target sound | Helper (autograde optional) | `sound-pick-word-stack` | planned | L1 | Core |
| **Sound Train** | Where is the sound — start, middle, or end of the word? | Auto | `sound-train` / `sound-at-position` | planned | L5 | Core — should recur (today it appears once) |
| **Rhyme Time** ★new | "Which of these rhymes with *bug*?" — pick from 3 pictures | Auto | `rhyme-match` (new) | **yes** | L5, then review rotation; anchor exercise for Module 0 | Core |
| **Sound Swap** ★new | Oral: "Say *mat*. Now change /m/ to /s/. What's the new word?" | Helper | `sound-swap` (new) | no (oral) | L6 | Core |
| **Syllable Clap** ★planned | Clap the beats in a spoken word | Helper | future | no | L43 (Module 5, two-syllable work) | Core |

## 2. See letters (grapheme recognition & formation)

| Exercise | Mechanic | Grading | Slide type | Reading game | Introduce | Tier |
|---|---|---|---|---|---|---|
| **Eagle Eyes** | Find the target letter among distractors | Auto | `find-grapheme` | **yes** | L1 | Core |
| **Letter Formation** | Watch and trace each letter stroke by stroke | Helper | `grapheme-trace-air` / `-palm` | **yes** | L1 | Core |
| **Letter Flash** | Letter appears; child names it / says its sound (flash cards) | Helper | `grapheme-recall`, `card-stack` | printables | L2 | Extra practice |

## 3. Map sounds ↔ letters

| Exercise | Mechanic | Grading | Slide type | Reading game | Introduce | Tier |
|---|---|---|---|---|---|---|
| **Letter Setter** | Hear a sound, choose the letter that makes it | Auto | `sound-to-grapheme` | **yes** | L2 | Core |
| **Lost Sounds** | The letters lost their sounds — child says each one back | Helper | `lost-sounds` | planned (practice mode) | L3 | Core |
| **Sound Sleuth** | Which of these words has the target sound in print? | Auto | `sound-in-word`, `identify-sound` | no | L6 | Core |

## 4. Blend words (decoding)

| Exercise | Mechanic | Grading | Slide type | Reading game | Introduce | Tier |
|---|---|---|---|---|---|---|
| **Finger Words** | Assign letters to fingers, blend along the knuckles | Helper | `finger-word`, `touch-slide` | no (physical) | L1 | Core |
| **Imaginary Finger Words** | Same, entirely mentally | Helper | `finger-word` (pre variant) | no | L5 | Core |
| **Word Chain** | RAN → RAM → RAMP: read each link as one grapheme changes | Helper | `word-chain` | no | L18 | Core |
| **Switcheroo** ★new | Two pictures (*bug* → *rug*); which letter must change to make the new word? | Auto | `letter-swap` (new) | **yes** | L18 (pairs with Word Chain) | Core |
| **Real or Silly?** ★planned | Decode a word, then decide: real word or silly word? | Helper | future | future | L15+ | Extra practice |

## 5. Build words (encoding / spelling)

| Exercise | Mechanic | Grading | Slide type | Reading game | Introduce | Tier |
|---|---|---|---|---|---|---|
| **Letter Boxes** | Reveal the word's letters, then fill the one missing box | Auto | `word-builder` (new, `mode: "missing"`) | **yes** (exists) | L8 | Core |
| **Word Builder** ★new | See the picture, hear the word, build it from a letter bank | Auto | `word-builder` (new, `mode: "full"`) | **yes** | L12 | Core |
| **Sentence Builder** ★planned | Arrange word tiles into the sentence the helper reads | Auto | future | future | L14+ (after Heart Words) | Core |

## 6. Read for meaning

| Exercise | Mechanic | Grading | Slide type | Reading game | Introduce | Tier |
|---|---|---|---|---|---|---|
| **Picture Quest** (word → picture) | Read the word, find its picture | Auto | `word-to-picture` | planned | L2 | Core |
| **Picture Quest** (picture → word) | See the picture, find its word | Auto | `picture-to-word` | planned | L16 | Core |
| **Word/Picture Grids** | Find all the words/pictures that match a rule | Config | `word-grid` / `picture-grid` | no | as needed | Extra practice |
| **Story Words** | Find and read the heart word inside real sentences | Helper | `story-words` | no | L14 | Core |
| **Comprehension Practice** | 2 questions at the end of every book (built into the reader) | Helper | book reader (built-in) | no | L1 | Core |

## 7. Recognize words automatically

| Exercise | Mechanic | Grading | Slide type | Reading game | Introduce | Tier |
|---|---|---|---|---|---|---|
| **Brain Words** | Rapid reread of the growing known-words list | Helper | `brain-words` | planned (timed practice) | L16 | Core |
| **Heart Words** | Learn by heart the words that don't follow the rules | Helper | `touch-slide` + `story-words` | printables (flash cards) | L14 | Core |

## 8. Read fluently

| Exercise | Mechanic | Grading | Slide type | Reading game | Introduce | Tier |
|---|---|---|---|---|---|---|
| **Narrative Ninja** | One sentence, three reads: accurate → modeled → with expression | Helper | `reading-fluency` | no | L17 | Core |
| **Book reading** | A real decodable book at the end of (nearly) every lesson | Helper | `books` | — | L1 | Core |

## 9. Program tools (not exercises)

| Tool | What it does | Status |
|---|---|---|
| **Teach Tam** | Child teaches today's concept to Tam (metacognitive check) | Live, L1 |
| **Jump Ahead** ★planned | Short placement experience (built from module review lessons) that tells a parent which lesson to start at | Roadmap — see GUIDE §10 |
| **Printables** | Tracing, flash cards, coloring | Live |

---

## Introduction timeline (what's available when)

| Lesson | New exercises unlocked |
|---|---|
| L1 | Elephant Ears, Eagle Eyes, Letter Formation, Finger Words, Book reading, Comprehension Practice, Teach Tam |
| L2 | Letter Setter, Picture Quest (word→picture), Letter Flash |
| L3 | Lost Sounds |
| L5 | Sound Train, **Rhyme Time**, Imaginary Finger Words |
| L6 | Sound Sleuth, **Sound Swap** |
| L8 | **Letter Boxes** (missing-letter) |
| L11 | Flash-card word stacks (`card-stack`) |
| L12 | **Word Builder** (full build) |
| L14 | Heart Words, Story Words, *Sentence Builder (planned)* |
| L16 | Brain Words, Picture Quest (picture→word) |
| L17 | Narrative Ninja |
| L18 | Word Chain, **Switcheroo** |
| L43 | *Syllable Clap (planned)* |

Rules of thumb:
1. An exercise enters a lesson only when the child can succeed at it with the cumulative set —
   Word Builder needs enough letters for rich words; Switcheroo needs word-chain thinking.
2. Once introduced, an exercise joins the review rotation and (if autogradable) should exist at
   `/reading-games` so parents can assign extra practice of exactly the weak skill.
3. Reading games are configured supersets (any letters/words), lessons use curated subsets.
4. Oral exercises (Rhyme Time, Sound Swap, Syllable Clap) are also the backbone of a future
   Module 0.

## Build status (July 2026)

- ✅ Live: everything unmarked in the tables above
- 🔨 This batch: `rhyme-match` (Rhyme Time), `letter-swap` (Switcheroo), `word-builder`
  (Word Builder + Letter Boxes slide), plus reading-game pages for Rhyme Time, Switcheroo, and
  Word Builder
- 📋 Next: Sound Swap slide, Sentence Builder, Real or Silly?, Elephant Ears / Picture Quest /
  Lost Sounds / Brain Words reading-game modes, Jump Ahead placement
- 🎨 Assets assumed: word images at `/l2r/words/{word}.png`, word audio at
  `{NEXT_PUBLIC_AUDIO}/l2r/words/{word}.mp3` (audio files pending — paths are wired, pretend they exist)
