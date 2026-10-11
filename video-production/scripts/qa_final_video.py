"""Inspect the actual exported film, without claiming a real-phone test.

Run after the MP4 render finishes. Runtime /generate is exercised only on the
isolated recording service (8006), while formal 8000 receives a read-only health
request. File hashes and logical record fingerprints protect production data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time

import httpx
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FILM = ROOT / "video-production"
FFMPEG = Path("D:/Codex/temp/day200-tools/ffmpeg-9.0.2-essentials_build/bin/ffmpeg.exe")
FFPROBE = FFMPEG.with_name("ffprobe.exe")
CHAPTERS = [("01 开场", 0, 15), ("02 首页", 15, 42), ("03 OCR建档", 42, 99),
            ("04 资料生命周期", 99, 129), ("05 耗材维护", 129, 164),
            ("06 双层AI", 164, 228), ("07 一物一码", 228, 253),
            ("08 统计开源", 253, 276), ("09 收尾", 276, 290)]


def command(args: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)


def fingerprint() -> dict:
    path = ROOT / "data/wusheng.db"
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        db.execute("BEGIN")
        tables = {}
        for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            rows = db.execute('SELECT * FROM "' + name.replace('"', '""') + '"').fetchall()
            serialized = sorted(json.dumps(row, ensure_ascii=False,
                                           default=lambda value: hashlib.sha256(value).hexdigest()) for row in rows)
            tables[name] = {"count": len(rows), "sha256": hashlib.sha256("\n".join(serialized).encode()).hexdigest()}
        db.rollback()
    return {"fileSha256": hashlib.sha256(path.read_bytes()).hexdigest(), "tables": tables}


def inspect_srt(path: Path, duration: float) -> dict:
    if not path.is_file():
        return {"exists": False, "passed": False, "path": str(path)}
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip())
    timings, warnings = [], []
    for index, block in enumerate(blocks, 1):
        lines = block.splitlines()
        if len(lines) < 3 or not re.fullmatch(r"\d+", lines[0]):
            warnings.append(f"Malformed caption block {index}")
            continue
        match = re.fullmatch(r"(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})", lines[1])
        if not match:
            warnings.append(f"Malformed caption time {index}")
            continue
        nums = [int(v) for v in match.groups()]
        start = nums[0] * 3600 + nums[1] * 60 + nums[2] + nums[3] / 1000
        end = nums[4] * 3600 + nums[5] * 60 + nums[6] + nums[7] / 1000
        if start >= end or end > duration + 0.1:
            warnings.append(f"Caption {index} exceeds its video bounds")
        if timings and start < timings[-1][1] - 0.05:
            warnings.append(f"Caption {index} overlaps previous caption")
        if len(lines[2:]) > 2:
            warnings.append(f"Caption {index} has more than two lines")
        timings.append((start, end))
    return {"exists": True, "path": str(path), "count": len(timings), "passed": bool(timings) and not warnings,
            "warnings": warnings, "firstStart": timings[0][0] if timings else None,
            "lastEnd": timings[-1][1] if timings else None,
            "scope": "Checks timing and layout structure; wording and synchronization still require viewing"}


def qa(video: Path, subtitles: Path, real_phone: Path | None) -> dict:
    if not video.is_file():
        raise SystemExit(f"Final MP4 is missing: {video}")
    reports = FILM / "reports"
    frames = FILM / "previews/qa-frames"
    frames.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    probe = command([str(FFPROBE), "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video)])
    if probe.returncode:
        raise RuntimeError(probe.stderr)
    metadata = json.loads(probe.stdout)
    (reports / "final-ffprobe.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    visual = next(s for s in metadata["streams"] if s["codec_type"] == "video")
    audio = next((s for s in metadata["streams"] if s["codec_type"] == "audio"), None)
    duration = float(metadata["format"]["duration"])
    numerator, denominator = visual["avg_frame_rate"].split("/")
    fps = float(numerator) / float(denominator)
    size = video.stat().st_size
    conditions = {"duration3To5Minutes": 180 <= duration <= 300,
                  "target290Seconds": abs(duration - 290) < 0.15,
                  "under300MBDecimal": size < 300_000_000,
                  "mp4Container": "mp4" in metadata["format"].get("format_name", ""),
                  "h264": visual["codec_name"] == "h264", "aac": audio is not None and audio["codec_name"] == "aac",
                  "fullHD": visual["width"] == 1920 and visual["height"] == 1080,
                  "fps30": abs(fps - 30) < 0.001, "yuv420p": visual.get("pix_fmt") == "yuv420p"}
    decode = command([str(FFMPEG), "-hide_banner", "-i", str(video), "-vf",
                      "blackdetect=d=0.3:pix_th=0.10,freezedetect=n=-50dB:d=3",
                      "-af", "volumedetect", "-f", "null", "NUL"], timeout=360)
    (reports / "final-full-decode.log").write_text(decode.stderr, encoding="utf-8")
    conditions["fullDecodeWithoutError"] = decode.returncode == 0 and not re.search(
        r"Error while decoding|Invalid data found|Conversion failed|corrupt decoded frame", decode.stderr, re.I)
    black = [{"start": float(a), "end": float(b), "duration": float(c)} for a, b, c in re.findall(
        r"black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)", decode.stderr)]
    freezes = re.findall(r"freeze_(?:start|end|duration):[^\n\r]+", decode.stderr)
    volumes = {label: float(value) for label, value in re.findall(r"(mean_volume|max_volume): ([-\d.]+) dB", decode.stderr)}
    conditions["noUnexpectedLongBlackIntervals"] = all(
        interval["duration"] <= 1 or interval["start"] >= duration - 2 for interval in black)
    conditions["audioNotSilent"] = volumes.get("max_volume", -100) > -45
    extracted = []
    for index, (name, start, end) in enumerate(CHAPTERS, 1):
        at = (start + end) / 2
        target = frames / f"chapter-{index:02d}-{at:06.2f}s.jpg"
        result = command([str(FFMPEG), "-hide_banner", "-loglevel", "error", "-ss", str(at), "-i", str(video),
                          "-frames:v", "1", "-q:v", "2", "-y", str(target)], timeout=45)
        if result.returncode:
            raise RuntimeError(f"Chapter {index} frame extraction failed: {result.stderr}")
        extracted.append({"chapter": name, "time": at, "path": str(target)})
    contact = Image.new("RGB", (1440, 3 * 304), "#eff4ed")
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
    except OSError:
        font = ImageFont.load_default()
    draw = ImageDraw.Draw(contact)
    for index, item in enumerate(extracted):
        frame = Image.open(item["path"]).convert("RGB")
        frame.thumbnail((472, 266))
        x, y = (index % 3) * 480 + 4, (index // 3) * 304 + 32
        contact.paste(frame, (x, y))
        draw.text((x + 4, y - 27), f'{item["chapter"]}  {item["time"]:.1f}s', fill="#244d34", font=font)
    sheet = frames / "nine-chapter-contact.jpg"
    contact.save(sheet, quality=94)
    runtime = {}
    with httpx.Client(trust_env=False, timeout=5) as client:
        for port in (8000, 8006, 8007):
            try:
                response = client.get(f"http://127.0.0.1:{port}/health")
                response.raise_for_status()
                runtime[str(port)] = {"health": response.json(), "request": "GET /health only"}
            except httpx.HTTPError as error:
                runtime[str(port)] = {"reachable": False, "error": str(error)}
        try:
            state = json.loads((FILM / "runtime/recording-state.json").read_text(encoding="utf-8"))
            response = client.post("http://127.0.0.1:8006/generate",
                                   json={"itemId": state["itemId"], "question": "这件物品有哪些关联耗材？"}, timeout=30)
            response.raise_for_status()
            body = response.json()
            runtime["evidenceActualGenerate"] = {"activeProvider": body.get("activeProvider"),
                                                 "modelInvoked": body.get("modelInvoked"),
                                                 "answer": body.get("answer"), "passed": bool(body.get("answer"))}
        except (httpx.HTTPError, OSError, KeyError, ValueError) as error:
            runtime["evidenceActualGenerate"] = {"passed": False, "error": str(error)}
    current = fingerprint()
    protection = json.loads((reports / "production-data-protection.json").read_text(encoding="utf-8"))
    unchanged = protection["before"]["tables"] == current["tables"]
    protection["finalQA"] = current
    protection["allTableRecordsUnchangedThroughFinalQA"] = unchanged
    protection["databaseFileUnchangedThroughFinalQA"] = protection["before"]["fileSha256"] == current["fileSha256"]
    (reports / "production-data-protection.json").write_text(json.dumps(protection, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"video": str(video.resolve()), "sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
              "durationSeconds": duration, "sizeBytes": size, "sizeMBDecimal": round(size / 1_000_000, 2),
              "resolution": [visual["width"], visual["height"]], "fps": fps,
              "videoCodec": visual["codec_name"], "audioCodec": audio["codec_name"] if audio else None,
              "conditions": conditions, "mediaTechnicalPassed": all(conditions.values()),
              "blackIntervals": black, "freezeSignals": freezes, "audioVolumeDB": volumes,
              "subtitles": inspect_srt(subtitles, duration), "chapterFrames": extracted, "contactSheet": str(sheet),
              "runtime": runtime, "productionRecordsUnchanged": unchanged,
              "realPhoneRecordingSupplied": bool(real_phone and real_phone.is_file()),
              "realPhoneTestClaimed": False,
              "manualReviewRequired": ["Check extracted frames and transitions at full size", "Listen to all narration and subtitle synchronization",
                                       "Check model answers match the actual recorded responses", "No real handset recording is inferred from a browser simulation"],
              "qaSeconds": round(time.monotonic() - started, 2)}
    (reports / "final-video-qa.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, default=FILM / "output/wusheng-aic-2026.mp4")
    parser.add_argument("--subtitles", type=Path, default=FILM / "subtitles/wusheng-zh-CN.srt")
    parser.add_argument("--phone-real-recording", type=Path)
    args = parser.parse_args()
    output = qa(args.video, args.subtitles, args.phone_real_recording)
    print(json.dumps({key: output[key] for key in ("video", "durationSeconds", "sizeMBDecimal", "fps", "resolution",
          "mediaTechnicalPassed", "subtitles", "productionRecordsUnchanged", "realPhoneRecordingSupplied", "contactSheet")}, ensure_ascii=False))
    raise SystemExit(0 if output["mediaTechnicalPassed"] and output["subtitles"]["passed"] and output["productionRecordsUnchanged"] else 1)
