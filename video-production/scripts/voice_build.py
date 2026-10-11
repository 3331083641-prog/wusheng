"""Build chapter narration and genuinely timed captions with free Edge Read Aloud.

Tool-only dependencies are separate from the app. Optional local proxy and
FFmpeg paths are supplied by environment or CLI. No keys or paid API are used.
The output is a synthetic Mandarin voice; it is not a human recording.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
SUBTITLES = ROOT / "subtitles"
FFMPEG = Path(os.environ.get("WUSHENG_VIDEO_FFMPEG") or shutil.which("ffmpeg") or "D:/Codex/temp/day200-tools/ffmpeg-9.0.2-essentials_build/bin/ffmpeg.exe")
FFPROBE = Path(os.environ.get("WUSHENG_VIDEO_FFPROBE") or str(FFMPEG.with_name("ffprobe.exe")))
SR = 48000


def run(*args: str) -> None:
    subprocess.run([str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y", *map(str, args)], check=True)


def duration(path: Path) -> float:
    output = subprocess.check_output([str(FFPROBE), "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(output)["format"]["duration"])


def read_wave(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as f:
        assert f.getframerate() == SR and f.getsampwidth() == 2 and f.getnchannels() == 1
        return np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float32) / 32768


def write_wave(path: Path, signal: np.ndarray) -> None:
    signal = np.clip(signal, -0.999, 0.999)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((signal * 32767).astype("<i2").tobytes())


def visible_width(text: str) -> float:
    return sum(1 if ord(c) > 255 else 0.55 for c in text)


def wrap_two_lines(text: str, max_width: float = 36) -> str:
    text = text.strip()
    if visible_width(text) <= max_width:
        return text
    candidates = [i + 1 for i, c in enumerate(text) if c in "，、：；。！？"]
    candidates = [i for i in candidates if 0 < i < len(text)]
    if not candidates:
        candidates = list(range(1, len(text)))
    split = min(candidates, key=lambda i: abs(visible_width(text[:i]) - visible_width(text[i:])))
    lines = [text[:split], text[split:]]
    assert all(visible_width(line) <= 40 for line in lines), text
    return "\n".join(lines)


def srt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


async def synthesize(chapter: dict, rate: str, voice: str, proxy: str | None) -> tuple[Path, list[dict]]:
    try:
        import edge_tts
    except ImportError:
        sys.path.insert(0, os.environ.get("WUSHENG_VIDEO_EDGE_TTS_PATH", "D:/Codex/tools/voice-edge-tts"))
        import edge_tts
    content = "\n".join(chapter["sentences"])
    # Neural voice can pronounce the two-word name more clearly with a space.
    spoken = content.replace("EvidenceProvider", "Evidence Provider")
    digest = hashlib.sha256((spoken + voice + rate).encode()).hexdigest()[:12]
    cache = AUDIO / "voice-cache"
    cache.mkdir(exist_ok=True)
    mp3 = cache / f"chapter-{chapter['id']:02}-{digest}.mp3"
    boundaries = mp3.with_suffix(".json")
    if mp3.exists() and boundaries.exists():
        return mp3, json.loads(boundaries.read_text(encoding="utf-8"))
    timings: list[dict] = []
    for attempt in range(5):
        communicate = edge_tts.Communicate(spoken, voice, rate=rate, proxy=proxy, boundary="SentenceBoundary", receive_timeout=45)
        timings = []
        try:
            with mp3.open("wb") as stream:
                async for part in communicate.stream():
                    if part["type"] == "audio":
                        stream.write(part["data"])
                    elif part["type"] == "SentenceBoundary":
                        timings.append({"text": part["text"], "start": part["offset"] / 10000000, "end": (part["offset"] + part["duration"]) / 10000000})
            break
        except Exception as exc:
            if attempt == 4:
                raise
            print(f"Chapter {chapter['id']}: transient {type(exc).__name__}, retrying", flush=True)
            await asyncio.sleep(3 + attempt * 2)
    boundaries.write_text(json.dumps(timings, ensure_ascii=False, indent=2), encoding="utf-8")
    return mp3, timings


async def build(proxy: str | None) -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    SUBTITLES.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / "storyboard/narration-script.json").read_text(encoding="utf-8"))
    voice = data["voicePreference"]
    full = np.zeros(round(data["duration"] * SR), dtype=np.float32)
    cues = []
    report = []
    for chapter in data["chapters"]:
        available = chapter["end"] - chapter["start"] - 1.2
        rate = -20
        mp3, timings = await synthesize(chapter, f"{rate:+d}%", voice, proxy)
        length = duration(mp3)
        if length > available:
            rate = math.ceil((1 + rate / 100) * length / available * 100 - 100)
            mp3, timings = await synthesize(chapter, f"{rate:+d}%", voice, proxy)
            length = duration(mp3)
        factor = max(1.0, length / available)
        if factor > 1.07:
            raise RuntimeError(f"Chapter {chapter['id']} would need excessive time compression: {factor}")
        wav = AUDIO / f"chapter-{chapter['id']:02}.wav"
        filters = f"atempo={factor:.8f},loudnorm=I=-18:TP=-2:LRA=7"
        run("-i", str(mp3), "-af", filters, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(wav))
        waveform = read_wave(wav)
        actual = len(waveform) / SR
        delay = 0.6
        insert = round((chapter["start"] + delay) * SR)
        full[insert:insert + len(waveform)] += waveform
        if chapter["start"] + delay + actual > chapter["end"] - 0.35:
            raise RuntimeError(f"Chapter {chapter['id']} exceeds time slot")
        for timing in timings:
            text = timing["text"].replace("Evidence Provider", "EvidenceProvider")
            # Timings are the actual sentence events from the synthesizer.
            start = chapter["start"] + delay + timing["start"] / factor
            end = chapter["start"] + delay + timing["end"] / factor
            cues.append({"chapter": chapter["id"], "start": round(start, 3), "end": round(end, 3), "text": wrap_two_lines(text)})
        report.append({"chapter": chapter["id"], "slotStart": chapter["start"], "slotEnd": chapter["end"], "voiceStart": round(chapter["start"] + delay, 3), "voiceEnd": round(chapter["start"] + delay + actual, 3), "voiceDuration": round(actual, 3), "rate": f"{rate:+d}%", "postTempo": factor, "characterCount": len(re.findall(r"[\u4e00-\u9fff]", "".join(chapter["sentences"])))})
        print(f"Chapter {chapter['id']}: {actual:.2f}s, voice rate {rate:+d}%, {len(timings)} captions", flush=True)
    # Service sentence durations may overlap the following sentence by 50 ms.
    # End the on-screen cue at the next real sentence event to prevent stacking.
    for current, following in zip(cues, cues[1:]):
        if current["end"] > following["start"]:
            current["end"] = round(following["start"] - 0.005, 3)
    write_wave(AUDIO / "narration.wav", full)
    run("-i", str(AUDIO / "narration.wav"), "-c:a", "aac", "-b:a", "192k", str(AUDIO / "narration.m4a"))
    official = [{"text": c["text"], "startMs": round(c["start"] * 1000), "endMs": round(c["end"] * 1000), "timestampMs": round((c["start"] + c["end"]) * 500), "confidence": None, "pageBreakAfter": True} for c in cues]
    (SUBTITLES / "captions.json").write_text(json.dumps(official, ensure_ascii=False, indent=2), encoding="utf-8")
    (SUBTITLES / "timeline.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2), encoding="utf-8")
    (SUBTITLES / "wusheng-zh-CN.srt").write_text("\n\n".join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}" for i, c in enumerate(cues, 1)) + "\n", encoding="utf-8-sig")
    (ROOT / "storyboard/voice-timeline.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (AUDIO / "voice-provenance.json").write_text(json.dumps({"engine": "edge-tts 7.2.8 / Microsoft Edge Read Aloud", "voice": voice, "synthetic": True, "paidService": False, "apiKeyUsed": False, "network": "existing local proxy; no credentials recorded", "duration": data["duration"], "sampleRate": SR, "alignment": "actual SentenceBoundary events; transformed by measured tempo factor", "chapters": report}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", default=os.environ.get("WUSHENG_VIDEO_TTS_PROXY"), help="Optional already configured local HTTP proxy; do not put credentials in source.")
    args = parser.parse_args()
    asyncio.run(build(args.proxy))
