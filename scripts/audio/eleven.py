"""ElevenLabs helpers for the course audio (bookroo/bookroo-phonics#615).

The key lives in ~/.config/bookroo/elevenlabs.env (ELEVENLABS_API_KEY); API
responses are cached by request in ~/.cache/bookroo/l2r-audio.

measure() trims silence and reports the clip's sounding length and how much of
it is voiced (periodic). A voiceless stop like /t/ should be short with ~0 ms
voiced; a long voiced stretch means the model added a vowel ("tuh").
"""
import hashlib
import json
import os
import subprocess
import urllib.request

import numpy as np

KEY = None
for line in open(os.path.expanduser("~/.config/bookroo/elevenlabs.env")):
    if line.startswith("ELEVENLABS_API_KEY="):
        KEY = line.split("=", 1)[1].strip().strip('"')
CACHE = os.path.expanduser("~/.cache/bookroo/l2r-audio")
os.makedirs(CACHE, exist_ok=True)


def tts(text, voice, model, fmt="mp3_44100_128", settings=None):
    body = {"text": text, "model_id": model}
    if settings:
        body["voice_settings"] = settings
    h = hashlib.sha1(json.dumps([body, voice, fmt], sort_keys=True).encode()).hexdigest()[:16]
    path = f"{CACHE}/{h}.mp3"
    if not os.path.exists(path):
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format={fmt}",
            data=json.dumps(body).encode(),
            headers={"xi-api-key": KEY, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            open(path, "wb").write(r.read())
    return path


def pcm(path, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-ac", "1", "-ar", str(sr),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768, sr


def frames(x, sr, win=0.025, hop=0.010):
    n, h = int(win * sr), int(hop * sr)
    return [x[i:i + n] for i in range(0, max(1, len(x) - n), h)], hop


def measure(path):
    x, sr = pcm(path)
    fs, hop = frames(x, sr)
    rms = np.array([np.sqrt(np.mean(f ** 2)) + 1e-9 for f in fs])
    db = 20 * np.log10(rms)
    loud = db > db.max() - 35
    if not loud.any():
        return {"ms": 0, "voiced_ms": 0}
    first, last = np.argmax(loud), len(loud) - np.argmax(loud[::-1]) - 1
    voiced = 0
    for f, l in zip(fs[first:last + 1], loud[first:last + 1]):
        if not l:
            continue
        f = f - f.mean()
        ac = np.correlate(f, f, "full")[len(f) - 1:]
        lo, hi = int(sr / 400), int(sr / 75)
        if ac[0] > 0 and ac[lo:hi].max() / ac[0] > 0.6:
            voiced += 1
    return {"ms": int((last - first + 1) * hop * 1000), "voiced_ms": int(voiced * hop * 1000)}


def analyze(x, sr):
    """Per 10 ms frame: overall level (dB) and low-band level (100-1000 Hz, dB).
    Vowels carry most of their energy in the low band; bursts, aspiration and
    s/sh/f/th noise carry almost none, so the low band finds the vowel."""
    fs, hop = frames(x, sr)
    db = np.array([20 * np.log10(np.sqrt(np.mean(f ** 2)) + 1e-9) for f in fs])
    n = len(fs[0])
    freqs = np.fft.rfftfreq(n, 1 / sr)
    band = (freqs >= 100) & (freqs <= 1000)
    win = np.hanning(n)
    low = np.array([10 * np.log10(np.sum(np.abs(np.fft.rfft(f * win))[band] ** 2) + 1e-12)
                    if len(f) == n else -120 for f in fs])
    return db, low, hop


def hf_share(x, sr, hop):
    """Per frame: dB share of energy above 4 kHz (s, sh and h noise live there)."""
    fs, _ = frames(x, sr)
    n = len(fs[0])
    f = np.fft.rfftfreq(n, 1 / sr)
    out = []
    for fr in fs:
        if len(fr) < n:
            out.append(-60.0)
            continue
        F = np.abs(np.fft.rfft(fr * np.hanning(n))) ** 2
        out.append(10 * np.log10(F[f > 4000].sum() / (F.sum() + 1e-12) + 1e-12))
    return np.array(out)


def vowel_onset(db, low, hop):
    """First of 3 frames in a row whose low band is within 10 dB of its peak."""
    hot = low > low.max() - 10
    for i in range(len(low) - 3):
        if hot[i:i + 3].all():
            return i
    return None


def write_clip(y, sr, out, fade_ms=10, pad_ms=60):
    n = int(sr * fade_ms / 1000)
    if len(y) > 2 * n:
        y = y.copy()
        y[:n] *= np.linspace(0, 1, n)
        y[-n:] *= np.linspace(1, 0, n)
    pad = np.zeros(int(sr * pad_ms / 1000), np.float32)
    y = np.concatenate([pad, y, pad])
    raw = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-",
                    "-b:a", "96k", out], input=raw, check=True)
    return out


def cut_onset(src, out, keep_ms=0):
    """Keep a word's opening consonant: sound start up to the vowel (+keep_ms)."""
    x, sr = pcm(src, 44100)
    db, voiced, hop = analyze(x, sr)
    start = int(np.argmax(db > db.max() - 35))
    v = vowel_onset(db, voiced, hop)
    # a voiced stop can run straight into its vowel; keep at least 50 ms
    end = int(max(v * hop + keep_ms / 1000, start * hop + 0.05) * sr)
    return write_clip(x[int(max(0, start - 1) * hop * sr):end], sr, out)


def cut_after_onset(src, out, back_ms=-5):
    """Drop a word's voiceless opening (s, h, k...) and keep the rest: sing -> ing."""
    x, sr = pcm(src, 44100)
    db, voiced, hop = analyze(x, sr)
    v = vowel_onset(db, voiced, hop)
    loud = db > db.max() - 35
    last = len(loud) - int(np.argmax(loud[::-1]))
    # step past any hiss left over from the dropped s/h: frames whose share of
    # energy above 4 kHz is well over the rest of the clip's typical share
    hf = hf_share(x, sr, hop)
    typical = np.median(hf[v:last])
    for _ in range(6):
        if hf[v] > typical + 10:
            v += 1
    return write_clip(x[int((v * hop - back_ms / 1000) * sr):int(last * hop * sr)], sr, out, fade_ms=15)


def cut_vowel(src, out, stretch=1.0):
    """Keep only the vowel of a word like 'sat' (from voicing onset until the
    level drops 15 dB below peak), optionally slowed without changing pitch."""
    x, sr = pcm(src, 44100)
    db, voiced, hop = analyze(x, sr)
    v = vowel_onset(db, voiced, hop)
    e = v
    while e < len(voiced) and voiced[e] > voiced.max() - 15:
        e += 1
    y = x[int((v * hop + 0.010) * sr):int(e * hop * sr)]
    if stretch != 1.0:
        raw = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
        y = np.frombuffer(subprocess.run(
            ["ffmpeg", "-v", "quiet", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-",
             "-af", f"rubberband=tempo={1 / stretch}", "-f", "s16le", "-"],
            input=raw, capture_output=True, check=True).stdout, dtype=np.int16).astype(np.float32) / 32768
    return write_clip(y, sr, out, fade_ms=25)


def cut_coda(src, out):
    """Keep what follows a word's vowel: math -> th."""
    x, sr = pcm(src, 44100)
    db, low, hop = analyze(x, sr)
    v = vowel_onset(db, low, hop)
    e = v
    while e < len(low) and low[e] > low.max() - 15:
        e += 1
    loud = db > db.max() - 40
    last = len(loud) - int(np.argmax(loud[::-1]))
    return write_clip(x[int(e * hop * sr):int(last * hop * sr)], sr, out, fade_ms=15)


WHISPER = "/Users/keslert/.cache/whisper-cpp/ggml-medium.en.bin"


def hear(path):
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", path, "-ar", "16000", "-ac", "1", os.path.join(CACHE, "whisper.wav")])
    return subprocess.run(["whisper-cli", "-m", WHISPER, "-f", os.path.join(CACHE, "whisper.wav"), "-nt", "-np"],
                          capture_output=True, text=True).stdout.strip()
