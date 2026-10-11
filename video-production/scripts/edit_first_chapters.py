"""Reproducible edits of the first three real UI recordings. No business data edits.

The edit decision list refers to original recording seconds. OCR waiting is cut,
not replaced; the on-screen disclosure is rendered by Chapter03 in Remotion.
PDF reading uses the actual Edge PDF popup recording, never a still screenshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = Path('D:/Python code/.venv/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe')
FFPROBE = ROOT / 'remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
FPS = 30


@dataclass(frozen=True)
class Cut:
    source: str
    start: float
    end: float
    frames: int
    purpose: str


EDL = {
    'ch02': [Cut('home', 1.75, 26.10, 810, 'Home carousel, navigation, scroll and return')],
    'ch03': [
        Cut('create', 2.60, 20.00, 731, 'Add item; all six images; begin real RapidOCR'),
        Cut('create', 88.80, 113.72, 979, 'Actual OCR result; source; manual confirmation; save; list'),
    ],
    'ch04': [
        Cut('detail', 2.30, 6.90, 174, 'Scene and product gallery photographs'),
        Cut('detail', 6.90, 12.35, 138, 'Evidence records; warranty category change'),
        Cut('detail', 12.35, 14.00, 49, 'Manual tab and actual PDF upload'),
        Cut('detail', 16.05, 19.25, 74, 'PDF extracted; persisted card; click viewer'),
        Cut('pdfPopup', 2.30, 6.30, 120, 'Actual Edge PDF reader, four continuous seconds'),
        Cut('detail', 29.20, 35.70, 163, 'Reloaded persistent archive and lifecycle'),
        Cut('detail', 35.70, 42.00, 182, 'Real archive export request and success'),
    ],
}


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.writing')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    tmp.replace(path)


def probe(path: Path):
    return json.loads(subprocess.check_output([
        str(FFPROBE), '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path),
    ], encoding='utf-8'))


def sha(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chapters', nargs='+', choices=list(EDL), default=list(EDL))
    parser.add_argument('--keep-intermediates', action='store_true')
    args = parser.parse_args()
    if not FFMPEG.is_file() or not FFPROBE.is_file():
        raise SystemExit('Existing full-filter FFmpeg 7.1 and Remotion FFprobe binaries are required.')
    captures = {s: read(ROOT / 'reports' / f'capture-{s}-raw.json') for s in ['home', 'create', 'detail']}
    state = read(ROOT / 'runtime/recording-state.json')
    sources = {s: Path(d['video']) for s, d in captures.items()}
    sources['pdfPopup'] = Path(state['pdfPopupVideo'])
    input_probes = {s: probe(p) for s, p in sources.items()}
    work = ROOT / 'recordings/edits/first-chapters'
    work.mkdir(parents=True, exist_ok=True)
    media = ROOT / 'remotion/public/media'
    media.mkdir(parents=True, exist_ok=True)
    focus = {'clips': {}}
    report = {
        'fps': FPS,
        'recordingsAreReal': True,
        'fakeScreensOrResponses': False,
        'ocrWaitRemovedSeconds': [20.0, 88.8],
        'pdfViewer': 'Actual Edge PDF popup recording; original PDF unchanged',
        'sources': {s: {'path': str(p), 'sha256': sha(p), 'duration': input_probes[s]['format'].get('duration')} for s, p in sources.items()},
        'chapters': {},
    }
    for chapter in args.chapters:
        segments = []
        decisions = []
        events = []
        running_frames = 0
        for n, cut in enumerate(EDL[chapter]):
            src = sources[cut.source]
            src_duration = float(input_probes[cut.source]['format']['duration'])
            if cut.end > src_duration + 0.001:
                raise ValueError(f'{cut.source} cut exceeds original duration')
            target_duration = cut.frames / FPS
            factor = target_duration / (cut.end - cut.start)
            if not 1 / 1.4 <= factor <= 1.401:
                raise ValueError(f'{chapter}/{n} speed change exceeds gentle range: {factor}')
            segment = work / f'{chapter}-{n:02d}.mp4'
            logfile = work / f'{chapter}-{n:02d}.log'
            filters = (
                f'setpts={factor:.12f}*(PTS-STARTPTS),fps={FPS},'
                f'tpad=stop_mode=clone:stop_duration=0.1,trim=end_frame={cut.frames},'
                'setpts=PTS-STARTPTS,setsar=1,format=yuv420p'
            )
            command = [str(FFMPEG), '-hide_banner', '-y', '-ss', str(cut.start),
                       '-t', str(cut.end - cut.start), '-i', str(src), '-an', '-vf', filters,
                       '-frames:v', str(cut.frames), '-r', str(FPS), '-fps_mode', 'cfr',
                       '-c:v', 'h264_nvenc', '-preset', 'p4',
                       '-cq', '18', '-b:v', '8M', '-maxrate', '12M', '-bufsize', '16M',
                       '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(segment)]
            print(f'{chapter} segment {n + 1}/{len(EDL[chapter])}: {cut.purpose}', flush=True)
            with logfile.open('w', encoding='utf-8') as log:
                subprocess.run(command, stdout=log, stderr=log, check=True)
            info = probe(segment)
            frames = int(info['streams'][0].get('nb_frames', 0))
            if frames != cut.frames:
                raise ValueError(f'{segment.name}: got {frames} frames; expected {cut.frames}')
            decisions.append({
                'source': cut.source, 'sourceStart': cut.start, 'sourceEnd': cut.end,
                'outputStart': running_frames / FPS, 'outputEnd': (running_frames + cut.frames) / FPS,
                'playbackSpeed': round(1 / factor, 6), 'purpose': cut.purpose,
                'maximumPaddingFrames': 3,
            })
            for mark in captures.get(cut.source, {}).get('marks', []):
                if 'x' in mark and 'y' in mark and cut.start <= mark['time'] < cut.end:
                    events.append({
                        'timeMs': round((running_frames / FPS + (mark['time'] - cut.start) * factor) * 1000),
                        'x': mark['x'] / 1920, 'y': mark['y'] / 1080, 'kind': 'click',
                        'label': mark['name'], 'sourceTime': mark['time'],
                    })
            running_frames += cut.frames
            segments.append(segment)
        concat_file = work / f'{chapter}-concat.txt'
        concat_file.write_text(''.join(f"file '{p.as_posix()}'\n" for p in segments), encoding='utf-8')
        output = media / f'{chapter}.mp4'
        with (work / f'{chapter}-concat.log').open('w', encoding='utf-8') as log:
            # Reset decoded-frame timestamps: copy-only concatenation of NVENC
            # GOPs can overlap B-frame DTS at the joins, despite exact lengths.
            subprocess.run([str(FFMPEG), '-hide_banner', '-y', '-f', 'concat', '-safe', '0',
                            '-i', str(concat_file), '-map', '0:v:0', '-an',
                            '-vf', f'setpts=N/({FPS}*TB),tpad=stop_mode=clone:stop_duration=0.1,trim=end_frame={running_frames},format=yuv420p',
                            '-r', str(FPS), '-fps_mode', 'cfr', '-frames:v', str(running_frames),
                            '-c:v', 'h264_nvenc', '-preset', 'p4', '-cq', '18', '-b:v', '8M',
                            '-maxrate', '12M', '-bufsize', '16M',
                            '-movflags', '+faststart', str(output)], stdout=log, stderr=log, check=True)
        final_probe = probe(output)
        stream = final_probe['streams'][0]
        if int(stream['nb_frames']) != running_frames or stream['width'] != 1920 or stream['height'] != 1080:
            raise ValueError(f'Final chapter validation failed: {chapter}')
        focus['clips'][chapter] = events
        report['chapters'][chapter] = {
            'output': str(output), 'sha256': sha(output), 'bytes': output.stat().st_size,
            'frames': running_frames, 'duration': running_frames / FPS,
            'codec': stream['codec_name'], 'pixelFormat': stream['pix_fmt'], 'edl': decisions,
        }
        if not args.keep_intermediates:
            for p in segments:
                p.unlink()
            concat_file.unlink()
        print(f'{chapter}: {running_frames / FPS:.3f}s, {running_frames} frames, {output.stat().st_size} bytes', flush=True)
    existing_own = read(media / 'focus-first-chapters.json') if (media / 'focus-first-chapters.json').exists() else {'clips': {}}
    existing_own.setdefault('clips', {}).update(focus['clips'])
    dump(media / 'focus-first-chapters.json', existing_own)
    combined = read(media / 'focus.json') if (media / 'focus.json').exists() else {'clips': {}}
    combined.setdefault('clips', {}).update(focus['clips'])
    dump(media / 'focus.json', combined)
    dump(ROOT / 'reports/first-chapters-edit.json', report)
    print('Wrote first-chapters-edit.json and real-coordinate focus metadata.', flush=True)


if __name__ == '__main__':
    main()
