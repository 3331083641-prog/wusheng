// Real Edge playback of the rendered local file; this is not a handset test.
import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const film = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const {chromium} = createRequire(path.join(film, '../frontend/package.json'))('@playwright/test');
const mode = process.argv[2] || 'final';
if (!['preview', 'final'].includes(mode)) throw new Error('Use preview or final');
const source = path.join(film, mode === 'final' ? 'output/wusheng-aic-2026.mp4' : 'previews/wusheng-aic-preview.mp4');
if (!fs.existsSync(source)) throw new Error('Rendered film is missing');
const html = path.join(film, `reports/${mode}-playback.html`);
fs.writeFileSync(html, `<!doctype html><meta charset="utf-8"><title>物生视频播放检查</title><style>html,body{margin:0;background:#edf3eb}video{display:block;width:100vw;height:100vh;object-fit:contain}</style><video controls src="${pathToFileURL(source).href}"></video>`);
const browser = await chromium.launch({channel: 'msedge', headless: true});
const page = await browser.newPage({viewport: {width: 1920, height: 1080}});
const errors = [];
page.on('pageerror', error => errors.push(error.message));
const stages = [];
try {
  await page.goto(pathToFileURL(html).href);
  await page.waitForFunction(() => document.querySelector('video').readyState >= 2);
  for (const at of [1, 30, 70, 114, 147, 175, 220, 240, 264, 283]) {
    const result = await page.evaluate(async seconds => {
      const video = document.querySelector('video');
      video.currentTime = seconds;
      await new Promise(resolve => video.addEventListener('seeked', resolve, {once: true}));
      const start = video.currentTime;
      await video.play();
      await new Promise(resolve => setTimeout(resolve, 850));
      video.pause();
      return {seek: seconds, advancedSeconds: video.currentTime - start, readyState: video.readyState,
        mediaError: video.error?.message || null, width: video.videoWidth, height: video.videoHeight};
    }, at);
    stages.push(result);
    if ([220, 240].includes(at)) await page.screenshot({path: path.join(film, `previews/${mode}-html5-${at}s.png`)});
  }
  const metadata = await page.evaluate(() => {
    const video = document.querySelector('video');
    return {duration: video.duration, decodedVideoFrames: video.getVideoPlaybackQuality().totalVideoFrames};
  });
  const passed = errors.length === 0 && stages.every(stage => stage.advancedSeconds > 0.2 && stage.readyState >= 3 && !stage.mediaError);
  const report = {actualHtml5Playback: true, browser: 'Installed Microsoft Edge', metadata, stages, pageErrors: errors, passed, physicalPhoneTest: false};
  fs.writeFileSync(path.join(film, `reports/${mode}-html5-seek.json`), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({mode, ...metadata, passed}));
  if (!passed) process.exitCode = 1;
} finally {
  await browser.close();
}
