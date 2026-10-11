"""Verify subtitle alignment, clean timing, text coverage and audio properties."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from voice_build import FFPROBE

script = json.loads((ROOT / "storyboard/narration-script.json").read_text(encoding="utf-8"))
timeline = json.loads((ROOT / "subtitles/timeline.json").read_text(encoding="utf-8"))
captions = json.loads((ROOT / "subtitles/captions.json").read_text(encoding="utf-8"))
chapters = json.loads((ROOT / "storyboard/voice-timeline.json").read_text(encoding="utf-8"))
norm = lambda text: re.sub(r"\s+", "", text)
text_pass = True
for chapter in script["chapters"]:
    expected = norm("".join(chapter["sentences"]))
    actual = norm("".join(c["text"] for c in timeline if c["chapter"] == chapter["id"]))
    if expected != actual:
        print("Caption text mismatch chapter", chapter["id"], expected, actual)
        text_pass = False
assert text_pass
for i, cue in enumerate(timeline):
    assert 0 <= cue["start"] < cue["end"] <= script["duration"]
    assert len(cue["text"].splitlines()) <= 2
    if i:
        assert cue["start"] >= timeline[i - 1]["end"] - .015
    chapter = script["chapters"][cue["chapter"] - 1]
    assert cue["start"] >= chapter["start"] and cue["end"] <= chapter["end"]
assert len(captions) == len(timeline)
audio = []
for filename in ["narration.wav", "bgm.wav", "narration-music.wav", "narration.m4a"]:
    path = ROOT / "audio" / filename
    probe = json.loads(subprocess.check_output([str(FFPROBE), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))
    length = float(probe["format"]["duration"])
    assert abs(length - 290) < .08, (filename, length)
    item = {"filename": filename, "duration": length, "sampleRate": int(probe["streams"][0]["sample_rate"]), "channels": int(probe["streams"][0]["channels"]), "codec": probe["streams"][0]["codec_name"], "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    if filename.endswith(".wav"):
        with wave.open(str(path), "rb") as stream:
            samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2").astype(np.float32) / 32768
        item["samplePeakDb"] = round(float(20 * np.log10(np.max(np.abs(samples)))), 2)
        item["clippedSamples"] = int(np.sum(np.abs(samples) >= .999))
        assert item["clippedSamples"] == 0
    audio.append(item)
characters = sum(c["characterCount"] for c in chapters)
report = {"pass": True, "chapters": len(chapters), "captionCues": len(timeline), "maximumCaptionLines": max(len(c["text"].splitlines()) for c in timeline), "subtitleTextMatchesScript": True, "subtitleAlignmentSource": "actual Microsoft neural TTS SentenceBoundary events", "allNarrationInsideChapterSlots": True, "duration": 290, "chineseCharacterCount": characters, "chineseCharactersPerMinuteOverFilm": round(characters / 290 * 60, 1), "syntheticVoice": "zh-CN-XiaoxiaoNeural", "audio": audio, "limits": ["This is synthetic voiceover, not a human speaker recording.", "Mobile sequence narration explicitly identifies browser emulation; real phone recording not supplied.", "Neural service transient network failures were retried; final outputs have complete sentence coverage."]}
(ROOT / "reports/voice-audio-qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
rows = ["# 中文旁白与字幕", "", "固定总长 04:50，30fps 视频基准。中文普通话合成音色：Microsoft XiaoxiaoNeural。每句字幕由真实合成句边界同步；最多两行。旁白与音乐分别保留，也提供组合音轨。", ""]
for chapter in script["chapters"]:
    rows += [f"## 第 {chapter['id']} 章 · {chapter['title']}（{chapter['start']:03d}—{chapter['end']:03d} 秒）", ""]
    for c in timeline:
        if c["chapter"] == chapter["id"]:
            rows.append(f"- {c['start']:.3f}—{c['end']:.3f}：{c['text'].replace(chr(10), ' ')}")
    rows += [""]
(ROOT / "storyboard/narration.md").write_text("\n".join(rows), encoding="utf-8")
print(json.dumps({key: report[key] for key in ['pass', 'chapters', 'captionCues', 'maximumCaptionLines', 'chineseCharacterCount', 'chineseCharactersPerMinuteOverFilm']}, ensure_ascii=False))
