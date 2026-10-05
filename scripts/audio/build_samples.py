"""Build SOUND_SAMPLES.html (bookroo/bookroo-phonics#615): candidate voices and the
single-sound methods, audio inlined so the page plays anywhere.

Usage: python3 scripts/audio/build_samples.py OUT_DIR
"""
import base64
import html
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eleven import cut_after_onset, cut_coda, cut_onset, cut_vowel, tts  # noqa: E402

os.makedirs(sys.argv[1], exist_ok=True)
os.chdir(sys.argv[1])
os.makedirs("samples", exist_ok=True)

VOICES = {  # ElevenLabs default voices (names from ElevenLabs' premade list)
    "Sarah": "EXAVITQu4vr4xnSDxMaL",
    "Matilda": "XrExE9yKIg1WjnnlVkGX",
    "Jessica": "cgSgspJ2msm6clMCkdW9",
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Chris": "iP95p4xoKVk53GoZ742B",
    "Liam": "TX3LPaxmHKxFdv7VOQHJ",
}
SOUND_VOICES = ["Sarah", "Matilda", "Chris"]
V4, V2 = "eleven_v4", "eleven_multilingual_v2"

LINES = [
    ("Encouragement", "Great job! Now let's read a book together."),
    ("Word: cat", "cat"),
    ("Word: ship", "ship"),
    ("Word: rabbit", "rabbit"),
]

# (row label, borrowed file or None, method label, builder(voice_id, out_path))
def stop(word, keep=0):
    return ("cut from “%s”" % word, lambda v, o: cut_onset(tts(word, v, V2), o, keep))


def held(text):
    return ("held: “%s”" % text, lambda v, o: shrink(tts(text, v, V4), o))


def vowel(word):
    return ("cut from “%s”, slowed" % word, lambda v, o: cut_vowel(tts(word, v, V2), o, stretch=2.5))


def chunk(word):
    return ("cut from “%s”" % word, lambda v, o: cut_after_onset(tts(word, v, V2), o))


def coda(word):
    return ("cut from the end of “%s”" % word, lambda v, o: cut_coda(tts(word, v, V2), o))


def name(letter):
    return ("says its name: “%s”" % letter, lambda v, o: shrink(tts(letter + ".", v, V4), o))


def shrink(src, out):
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", src, "-b:a", "96k", out], check=True)
    return out


SOUNDS = [
    ("Stops (the hard ones)", [
        ("/t/", "t", *stop("top")), ("/p/", "p", *stop("pot")), ("/k/", "k", *stop("cot")),
        ("/b/", "b", *stop("bot", 25)), ("/d/", "d", *stop("dot", 25)), ("/g/", "g", *stop("got", 25)),
        ("/ch/", None, *stop("chop")), ("/j/", "j", *stop("jot", 25)),
    ]),
    ("Sounds you can stretch", [
        ("/m/", "m", *held("Mmmmmm.")), ("/n/", "n", *held("Nnnnnn.")), ("/s/", "s", *held("Ssssss.")),
        ("/z/", "z", *held("Zzzzzz.")), ("/f/", "f", *held("Ffffff.")), ("/v/", "v", *held("Vvvvvv.")),
        ("/l/", "l", *held("Llllll.")), ("/sh/", None, *held("Shhhhh.")),
        ("/th/ (thin)", None, *coda("math")), ("/th/ (this)", None, *coda("bathe")),
    ]),
    ("Short vowels", [
        ("/ă/ apple", "a", *vowel("sat")), ("/ĕ/ egg", "e", *vowel("set")), ("/ĭ/ itch", "i", *vowel("sit")),
        ("/ŏ/ octopus", "o", *vowel("sock")), ("/ŭ/ up", "u", *vowel("sup")),
    ]),
    ("Long vowels (say their names)", [
        ("/ā/", "A", *name("A")), ("/ē/", None, *name("E")), ("/ī/", None, *name("Eye")),
        ("/ō/", None, *name("O")), ("/ū/", None, *name("U")),
    ]),
    ("Glued chunks", [
        ("/ing/", None, *chunk("sing")), ("/ank/", None, *chunk("sank")),
        ("/ang/", None, *chunk("sang")), ("/old/", None, *chunk("sold")),
    ]),
]


def audio(path):
    data = base64.b64encode(open(path, "rb").read()).decode()
    return f"<audio controls preload='none' src='data:audio/mpeg;base64,{data}'></audio>"


def slug(s):
    return "".join(c if c.isalnum() else "-" for c in s).strip("-").lower()


voice_rows = []
for vname, vid in VOICES.items():
    cells = []
    for label, text in LINES:
        out = f"samples/voice-{slug(vname)}-{slug(label)}.mp3"
        cells.append(f"<td>{audio(shrink(tts(text, vid, V4), out))}</td>")
    voice_rows.append(f"<tr><th>{vname}</th>{''.join(cells)}</tr>")

sound_sections = []
for title, rows in SOUNDS:
    body = []
    for label, borrowed, method, build in rows:
        cells = []
        for vname in SOUND_VOICES:
            out = f"samples/{slug(vname)}-{slug(label)}.mp3"
            cells.append(f"<td>{audio(build(VOICES[vname], out))}</td>")
        os.makedirs("ref", exist_ok=True)
        ref = f"ref/{borrowed}.mp3" if borrowed else None
        if borrowed and not os.path.exists(ref):
            subprocess.run(["curl", "-s", "-o", ref, f"https://images.bookroo.com/l2r/sounds/{borrowed}.mp3"])
        cells.append(f"<td>{audio(ref) if ref else '<span class=none>none</span>'}</td>")
        body.append(f"<tr><th>{html.escape(label)}<small>{html.escape(method)}</small></th>{''.join(cells)}</tr>")
    head = "".join(f"<th>{v}</th>" for v in SOUND_VOICES)
    sound_sections.append(
        f"<h3>{title}</h3><table><tr><th></th>{head}<th>Current (borrowed)</th></tr>{''.join(body)}</table>")

page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Learn to Read — ElevenLabs sound samples</title>
<style>
body {{ font-family: ui-sans-serif, -apple-system, sans-serif; font-size: 14px; color: #212622; background: #faf9f5; margin: 24px; max-width: 1100px; }}
h1 {{ font-size: 22px; margin: 0 0 6px; }} h2 {{ font-size: 17px; margin: 28px 0 6px; }} h3 {{ font-size: 14px; margin: 18px 0 6px; color: #3c443e; }}
p {{ color: #3c443e; line-height: 1.5; max-width: 820px; margin: 0 0 8px; }}
table {{ border-collapse: collapse; background: #fff; }}
th, td {{ border-bottom: 1px solid #eee9de; padding: 6px 10px; text-align: left; vertical-align: middle; }}
tr:first-child th {{ font-size: 12px; color: #6b746d; }}
th small {{ display: block; font-weight: 400; color: #8a938c; font-size: 11px; }}
audio {{ height: 32px; width: 200px; }}
.none {{ color: #b0b5ae; font-size: 12px; }}
</style></head><body>
<h1>Learn to Read — ElevenLabs sound samples</h1>
<p>Two choices: the <b>voice</b> for the whole course (sounds, words, and any spoken prompts), and whether
the <b>single sounds</b> below are clean enough to ship. Listen with headphones.</p>
<h2>1. Pick a voice</h2>
<p>Six ElevenLabs default voices, newest model (Eleven v4).</p>
<table><tr><th></th>{''.join(f'<th>{html.escape(l)}</th>' for l, _ in LINES)}</tr>{''.join(voice_rows)}</table>
<h2>2. Are these single sounds clean?</h2>
<p>ElevenLabs reads words well but has no way to ask for a lone sound: asked for /t/ directly it says
“tuh”, or the letter name, or reads the slashes aloud. So each kind of sound uses a different trick, shown
under its name:</p>
<p><b>Stops</b> (t, p, k, b, d, g): the voice says a word (“top”) and the clip keeps only the part before the
vowel. Listen for a crisp sound with no “uh”; b, d and g keep a sliver of the vowel so they're audible.
<b>Sounds you can stretch</b> (m, s, sh…): the voice says “Mmmmmm.” <b>Short vowels</b>: cut from a word and
slowed down. <b>Long vowels</b>: the letter name. <b>Chunks</b>: “sing” minus the s.</p>
<p>The last column is the current, borrowed recording where one exists. If the stops aren't clean in any
voice, the fallback is recording those eight sounds once yourself and converting them to the chosen voice
with ElevenLabs' voice changer.</p>
{''.join(sound_sections)}
</body></html>"""
open("SOUND_SAMPLES.html", "w").write(page)
print(os.path.abspath("SOUND_SAMPLES.html"), os.path.getsize("SOUND_SAMPLES.html"), "bytes")
