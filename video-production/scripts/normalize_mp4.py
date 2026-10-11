"""Normalize a local rendered film for common H.264/AAC players.

Keep the rendered master, validate a separate candidate, then replace atomically.
Never relax the final QA's yuv420p requirement to accept full-range yuvj420p.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

FILM = Path(__file__).resolve().parents[1]
FF = os.environ.get('WUSHENG_VIDEO_FFMPEG', 'D:/Python code/.venv/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe')
PROBE = os.environ.get('WUSHENG_VIDEO_FFPROBE', 'D:/Codex/temp/day200-tools/ffmpeg-9.0.2-essentials_build/bin/ffprobe.exe')


def metadata(path):
    return json.loads(subprocess.check_output([PROBE, '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)], text=True, encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, help='Validate an already encoded local candidate rather than encoding again')
    args = parser.parse_args()
    source = FILM / 'output/wusheng-aic-2026.mp4'
    original = metadata(source)
    video = next(s for s in original['streams'] if s['codec_type'] == 'video')
    if video['pix_fmt'] == 'yuv420p':
        print('Already yuv420p; original file unchanged')
        return
    candidate = (args.candidate or source.with_suffix('.normalized.mp4')).resolve()
    if candidate.parent != (FILM / 'output').resolve() or candidate == source.resolve():
        raise SystemExit('Candidate must be a separate file inside the video output directory')
    master = FILM / 'previews/remotion-render-master.mp4'
    if master.exists():
        raise SystemExit('Rendered master already exists; no original was overwritten')
    if not args.candidate:
        encoder = os.environ.get('WUSHENG_VIDEO_ENCODER', 'libx264')
        preset = 'p6' if encoder == 'h264_nvenc' else 'medium'
        filter_chain = 'scale=in_range=pc:out_range=tv,format=yuv420p' if video.get('color_range') == 'pc' else 'format=yuv420p'
        subprocess.run([FF, '-hide_banner', '-loglevel', 'warning', '-i', str(source), '-map', '0:v:0', '-map', '0:a:0',
                        '-vf', filter_chain, '-c:v', encoder, '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-color_range', 'tv',
                        '-preset', preset, '-b:v', '5500k', '-maxrate', '7000k', '-bufsize', '11000k',
                        '-c:a', 'copy', '-movflags', '+faststart', '-y', str(candidate)], check=True)
    converted = metadata(candidate)
    target = next(s for s in converted['streams'] if s['codec_type'] == 'video')
    assert target['pix_fmt'] == 'yuv420p' and target['codec_name'] == 'h264'
    assert target['width'] == 1920 and target['height'] == 1080 and int(target['nb_frames']) == 8700
    assert any(s['codec_type'] == 'audio' and s['codec_name'] == 'aac' for s in converted['streams'])
    assert abs(float(converted['format']['duration']) - 290) < .15 and candidate.stat().st_size < 300_000_000
    report = {'originalSHA256': sha(source), 'normalizedSHA256': sha(candidate), 'originalPixelFormat': video['pix_fmt'],
              'pixelFormat': target['pix_fmt'], 'colorRange': target.get('color_range'),
              'audioCopied': True, 'frames': int(target['nb_frames']), 'contentChanges': False,
              'method': 'FFmpeg color-range normalization; AAC stream copied; original master retained'}
    source.replace(master)
    try:
        candidate.replace(source)
    except BaseException:
        master.replace(source)
        raise
    (FILM / 'reports/normalization.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
