"""Original warm instrumental bed. No external recordings, samples or melody.

Deterministic synthesis: soft piano/air pad, D major, 88 BPM. CC0-1.0.
Mixed delivery is intentionally much quieter than narration.
"""
from pathlib import Path
import subprocess
import sys

import numpy as np

from voice_build import AUDIO, FFMPEG, SR, read_wave, run, write_wave

DURATION = 290
AUDIO.mkdir(parents=True, exist_ok=True)
BEAT = 60 / 88
BAR = 4 * BEAT
rng = np.random.default_rng(20261011)
track = np.zeros((DURATION * SR, 2), dtype=np.float32)


def add_note(midi, start, length, gain, pan=0.0, pad=False):
    offset = int(start * SR)
    count = min(int(length * SR), len(track) - offset)
    if count <= 0:
        return
    t = np.arange(count, dtype=np.float32) / SR
    f = 440 * 2 ** ((midi - 69) / 12)
    if pad:
        tone = (np.sin(2 * np.pi * f * t) + .21 * np.sin(2 * np.pi * f * 2 * t + .13)) / 1.21
        env = np.minimum(t / .8, 1) * np.minimum((length - t) / 1.0, 1)
    else:
        tone = (np.sin(2 * np.pi * f * t) + .28 * np.sin(2 * np.pi * f * 2 * t) + .07 * np.sin(2 * np.pi * f * 3 * t)) / 1.35
        env = (1 - np.exp(-t * 95)) * np.exp(-t * 2.0) * np.minimum((length - t) / .2, 1)
    signal = tone * env * gain
    track[offset:offset + count, 0] += signal * np.sqrt((1 - pan) / 2)
    track[offset:offset + count, 1] += signal * np.sqrt((1 + pan) / 2)


# Diatonic original harmonic/arpeggio pattern, not a borrowed composition.
chords = [([50, 57, 61, 64, 66], 38), ([47, 54, 57, 62, 66], 35), ([43, 50, 54, 57, 62], 31), ([45, 52, 57, 59, 64], 33)]
bar_count = int(DURATION / BAR) + 1
for bar_index in range(bar_count):
    chord, bass = chords[bar_index % 4]
    start = bar_index * BAR
    for j, note in enumerate(chord[:4]):
        add_note(note, start, BAR + 1.1, .017, (j - 1.5) * .25, pad=True)
    add_note(bass, start, BAR * .9, .055, -.1)
    pattern = [0, 2, 1, 4, 2, 3]
    times = [0.0, .75, 1.5, 2.0, 2.75, 3.5]
    if bar_index % 8 == 7:
        pattern = [1, 2, 3, 4]
        times = [0.0, 1.0, 2.0, 3.0]
    for note_index, beats in zip(pattern, times):
        add_note(chord[note_index] + 12, start + beats * BEAT, BEAT * 2.5, .048, np.sin(bar_index * .8 + beats) * .4)
    # A soft rhythmic tap, well below both piano and voice.
    for beat in (0, 2):
        when = int((start + beat * BEAT) * SR)
        count = min(int(.14 * SR), len(track) - when)
        if count <= 0:
            continue
        tt = np.arange(count, dtype=np.float32) / SR
        tap = .012 * np.sin(2 * np.pi * 62 * tt) * np.exp(-tt * 45)
        track[when:when + count] += tap[:, None]

fade_in = np.minimum(np.arange(len(track)) / (SR * 3), 1)
fade_out = np.minimum((len(track) - np.arange(len(track))) / (SR * 7), 1)
track *= (fade_in * fade_out)[:, None]
raw = AUDIO / "bgm-original-master.wav"
import wave
with wave.open(str(raw), "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes((np.clip(track, -.999, .999) * 32767).astype("<i2").tobytes())
run("-i", str(raw), "-af", "loudnorm=I=-34:TP=-8:LRA=6", "-ar", str(SR), "-c:a", "pcm_s16le", str(AUDIO / "bgm.wav"))
if (AUDIO / "narration.wav").exists():
    run("-i", str(AUDIO / "narration.wav"), "-i", str(AUDIO / "bgm.wav"), "-filter_complex", "[0:a]pan=stereo|c0=c0|c1=c0[v];[v][1:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[out]", "-map", "[out]", "-ar", str(SR), "-c:a", "pcm_s16le", str(AUDIO / "narration-music.wav"))
print("Original BGM complete: 290 seconds, 88 BPM, D major; delivery integrated loudness -34 LUFS")
