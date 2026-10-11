import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';

const project = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const production = path.resolve(project, '..');
const mode = process.argv[2] || 'preview';
const browserExecutable = process.env.WUSHENG_VIDEO_BROWSER || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const inputProps = {qwenModel: 'qwen3-vl:4b-instruct-q4_K_M'};
const required = [
  'images/logo.svg', 'images/product.png', 'images/order.png', 'images/manual_image.png', 'images/warranty.png', 'images/cleaner.png',
  'media/ch02.mp4', 'media/ch03.mp4', 'media/ch04.mp4', 'media/ch05.mp4', 'media/ch06-evidence.mp4', 'media/ch06-qwen.mp4', 'media/ch07.mp4', 'media/ch07-mobile.mp4', 'media/ch08.mp4', 'media/ch09.mp4',
  'audio/narration-music.wav', 'subtitles/captions.json',
];
const missing = required.filter((name) => !fs.existsSync(path.join(project, 'public', name)));
if (missing.length) throw new Error(`正式媒体尚未齐备：\n${missing.join('\n')}`);
if (!fs.existsSync(browserExecutable)) throw new Error(`浏览器不存在：${browserExecutable}`);
const captions = JSON.parse(fs.readFileSync(path.join(project, 'public/subtitles/captions.json'), 'utf8'));
for (const cue of Array.isArray(captions) ? captions : captions.captions) {
  if (cue.text.split('\n').length > 2 || cue.text.length > 86) throw new Error(`字幕超过两行安全长度：${cue.text}`);
  if (!(cue.endMs > cue.startMs && cue.startMs >= 0 && cue.endMs <= 290000)) throw new Error('字幕时间超出主片范围');
}

let lastBundle = -1;
const serveUrl = await bundle({entryPoint: path.join(project, 'src/index.ts'), publicDir: path.join(project, 'public'), onProgress: (value) => {
  const rounded = Math.floor(value / 10) * 10;
  if (rounded !== lastBundle) {console.log(`Bundling ${rounded}%`); lastBundle = rounded;}
}});
const composition = await selectComposition({serveUrl, id: 'WushengAIC', inputProps, browserExecutable, timeoutInMilliseconds: 60000});

if (mode === 'stills') {
  const frames = process.argv.slice(3).length ? process.argv.slice(3).map(Number) : [60, 330, 720, 2100, 3240, 4350, 5520, 6060, 7200, 8040, 8610];
  const directory = path.join(production, 'previews', 'qa-frames');
  fs.mkdirSync(directory, {recursive: true});
  for (const frame of frames) {
    await renderStill({serveUrl, composition, inputProps, browserExecutable, frame, imageFormat: 'png', output: path.join(directory, `frame-${String(frame).padStart(5, '0')}.png`), timeoutInMilliseconds: 60000});
    console.log(`Still ${frame}`);
  }
} else {
  const preview = mode === 'preview';
  if (!preview && mode !== 'final') throw new Error('使用 preview、final 或 stills 模式。');
  const outputLocation = path.join(production, preview ? 'previews/wusheng-aic-preview.mp4' : 'output/wusheng-aic-2026.mp4');
  fs.mkdirSync(path.dirname(outputLocation), {recursive: true});
  let lastPercent = -1;
  await renderMedia({serveUrl, composition, inputProps, browserExecutable, outputLocation,
    codec: 'h264', audioCodec: 'aac', pixelFormat: 'yuv420p', videoBitrate: preview ? '1300k' : '5500k', audioBitrate: '128k',
    scale: preview ? 0.5 : 1, concurrency: 4, imageFormat: 'jpeg', jpegQuality: 94, hardwareAcceleration: 'if-possible', timeoutInMilliseconds: 60000,
    onProgress: ({progress}) => {
      const percent = Math.floor(progress * 100);
      if (percent !== lastPercent) {console.log(`Rendering ${percent}%`); lastPercent = percent;}
    },
  });
  const bytes = fs.statSync(outputLocation).size;
  const report = {outputLocation, mode, durationSeconds: 290, frames: 8700, fps: 30, width: preview ? 960 : 1920, height: preview ? 540 : 1080, bytes, maximumBytes: 300000000, withinSizeLimit: bytes <= 300000000, renderedAt: new Date().toISOString(), composition: 'WushengAIC', browserExecutable, actualValidationRequired: '请进一步运行 FFprobe 和全片音画 QA。'};
  fs.mkdirSync(path.join(production, 'reports'), {recursive: true});
  fs.writeFileSync(path.join(production, 'reports', `render-${mode}.json`), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
  if (bytes > 300000000) throw new Error('成片超过官方 300MB 限制，需要压缩后复核。');
}
