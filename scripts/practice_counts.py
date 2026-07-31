#!/usr/bin/env python3
"""Shared counting of practiced words in lesson JSON slides.

Used by build-word-matrix.py and availability.py so both agree on what
counts as practice and which slide types are reading vs listening.
"""

import glob
import json
import os
import re
from collections import Counter

WORD_RE = re.compile(r"[a-z]+(?:['’][a-z]+)*")


def norm(word):
    """Lowercase and keep only letters/internal apostrophes."""
    m = WORD_RE.search(str(word).lower().replace("’", "'"))
    return m.group(0) if m else None


def tokenize(text):
    return WORD_RE.findall(str(text).lower().replace("’", "'"))


def words_in_slide(slide):
    """Yield (word, is_reading) for each practiced-word occurrence.

    Counted: words the child reads, blends, or listens for; is_reading is
    False for listening-only exercises (the word need not be decodable yet).
    Not counted: distractor picture labels, parent script, book ids.
    """
    t = slide.get("type")
    if t in ("finger-word", "touch-slide", "picture-to-word"):
        yield norm(slide["word"]), True
    elif t == "word-to-picture":
        for s in slide.get("sets", []):
            yield norm(s["word"]), True
    elif t == "sound-pick-word-stack":
        # Elephant Ears — the parent says the word aloud; the child listens
        # for the target sound. The revealed card is for the parent to read.
        for entry in slide.get("words", []):
            yield norm("".join(g for g, _ in entry)), False
    elif t in ("card-stack",):
        for w in slide.get("values", []):
            yield norm(w), True
    elif t in ("brain-words", "word-chain"):
        for w in slide.get("words", []):
            yield norm(w), True
    elif t == "sound-at-position":
        # Elephant Ears — the child listens for the sound, no reading.
        for w in slide.get("words", []):
            yield norm(w["word"]), False
    elif t == "story-words":
        # The parent reads the story; the child only finds the target words.
        targets = {norm(w) for w in slide.get("words", [])}
        for tok in tokenize(slide.get("story", "")):
            if tok in targets:
                yield tok, True
    elif t == "reading-fluency":
        yield from ((tok, True) for tok in tokenize(slide.get("text", "")))


def load_lesson_files(root):
    """[(file_number, counts, read_counts, reading_slides)] for each
    lessons/lesson-N.json, where reading_slides maps word -> [slide types]."""
    out = []
    for path in sorted(
            glob.glob(os.path.join(root, "lessons", "lesson-*.json")),
            key=lambda p: int(re.search(r"(\d+)", os.path.basename(p)).group(1))):
        number = int(re.search(r"(\d+)", os.path.basename(path)).group(1))
        counts, read_counts = Counter(), Counter()
        reading_slides = {}
        for slide in json.load(open(path)):
            for w, is_reading in words_in_slide(slide):
                if not w:
                    continue
                counts[w] += 1
                if is_reading:
                    read_counts[w] += 1
                    reading_slides.setdefault(w, []).append(slide.get("type"))
        out.append((number, counts, read_counts, reading_slides))
    return out


# Lesson file numbers match curriculum lesson numbers 1:1 (files were
# renamed to the curriculum order on 2026-07-30; the old lesson-map.json
# sidecar is gone).
